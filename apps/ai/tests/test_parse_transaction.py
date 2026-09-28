import json
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.categories.tests.factories import CategoryFactory
from apps.transactions.models import Transaction
from apps.users.tests.factories import UserFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/parse-transaction/"


@pytest.mark.django_db
class TestParseTransaction:
    @patch("apps.ai.llm.generate")
    def test_valid_parse_returns_proposed_transaction_without_saving(self, mock_generate):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        category = CategoryFactory(user=user, type="expense")
        mock_generate.return_value = json.dumps(
            {
                "type": "expense",
                "amount": 42.5,
                "currency": "USD",
                "account_id": str(account.id),
                "category_id": str(category.id),
                "merchant": "Starbucks",
                "description": "coffee",
                "transaction_date": "2026-09-27",
                "clarification": "",
            }
        )

        response = authed_client(user).post(URL, {"text": "Spent $42.50 at Starbucks yesterday"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["valid"] is True
        assert data["transaction"]["account"] == str(account.id)
        assert data["transaction"]["category"] == str(category.id)
        assert data["transaction"]["amount"] == "42.50"
        assert data["needs_clarification"] is None
        assert Transaction.objects.count() == 0  # AI output never writes to the DB (spec §20)

    @patch("apps.ai.llm.generate")
    def test_missing_account_asks_for_clarification(self, mock_generate):
        user = UserFactory()
        mock_generate.return_value = json.dumps(
            {
                "type": "expense",
                "amount": 10,
                "account_id": None,
                "category_id": None,
                "transaction_date": "2026-09-27",
                "clarification": "Which account did you use?",
            }
        )

        response = authed_client(user).post(URL, {"text": "Spent $10 on lunch"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["valid"] is False
        assert data["needs_clarification"] == "Which account did you use?"
        assert data["transaction"]["account"] is None

    @patch("apps.ai.llm.generate")
    def test_account_belonging_to_another_user_is_not_accepted(self, mock_generate):
        user = UserFactory()
        other_user = UserFactory()
        other_account = AccountFactory(user=other_user, currency="USD")
        mock_generate.return_value = json.dumps(
            {
                "type": "expense",
                "amount": 10,
                "account_id": str(other_account.id),
                "category_id": None,
                "transaction_date": "2026-09-27",
                "clarification": "",
            }
        )

        response = authed_client(user).post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["valid"] is False
        assert data["transaction"]["account"] is None
        assert Transaction.objects.count() == 0

    @patch("apps.ai.llm.generate")
    def test_hallucinated_category_is_dropped_not_fatal(self, mock_generate):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        mock_generate.return_value = json.dumps(
            {
                "type": "expense",
                "amount": 10,
                "currency": "USD",
                "account_id": str(account.id),
                "category_id": "11111111-1111-1111-1111-111111111111",
                "transaction_date": "2026-09-27",
                "clarification": "",
            }
        )

        response = authed_client(user).post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["valid"] is True
        assert data["transaction"]["category"] is None

    @patch("apps.ai.llm.generate")
    def test_business_rule_violation_is_reported_not_saved(self, mock_generate):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        mock_generate.return_value = json.dumps(
            {
                "type": "adjustment",
                "amount": 0,
                "currency": "USD",
                "account_id": str(account.id),
                "category_id": None,
                "transaction_date": "2026-09-27",
                "clarification": "",
            }
        )

        response = authed_client(user).post(URL, {"text": "Correct my balance"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["valid"] is False
        assert "amount" in data["errors"]
        assert Transaction.objects.count() == 0

    @patch("apps.ai.llm.generate")
    def test_malformed_llm_json_returns_ai_service_error(self, mock_generate):
        user = UserFactory()
        mock_generate.return_value = "not json at all"

        response = authed_client(user).post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 502
        assert response.data["error"]["code"] == "AI_SERVICE_ERROR"

    @patch("apps.ai.llm.generate")
    def test_llm_rate_limited_returns_distinct_error(self, mock_generate):
        from apps.ai.llm import LLMRateLimitedError

        user = UserFactory()
        mock_generate.side_effect = LLMRateLimitedError("rate limited")

        response = authed_client(user).post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 503
        assert response.data["error"]["code"] == "AI_RATE_LIMITED"

    @patch("apps.ai.llm.generate")
    def test_daily_quota_blocks_before_calling_llm(self, mock_generate, settings):
        settings.AI_DAILY_REQUEST_LIMIT = 0
        user = UserFactory()

        response = authed_client(user).post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 429
        mock_generate.assert_not_called()

    def test_requires_authentication(self):
        response = APIClient().post(URL, {"text": "Spent $10 somewhere"})

        assert response.status_code == 401
