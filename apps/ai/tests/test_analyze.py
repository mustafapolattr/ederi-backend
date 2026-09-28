from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.ai.models import AIUsageLog
from apps.categories.tests.factories import CategoryFactory
from apps.transactions.tests.factories import TransactionFactory
from apps.transactions.models import Transaction
from apps.users.tests.factories import UserFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/analyze/"


@pytest.mark.django_db
class TestAnalyze:
    @patch("apps.ai.llm.generate")
    def test_facts_are_backend_computed_regardless_of_llm_output(self, mock_generate):
        user = UserFactory()
        category = CategoryFactory(user=user, type="expense", name="Dining")
        account = AccountFactory(user=user, currency="USD")
        TransactionFactory(
            user=user,
            account=account,
            category=category,
            type=Transaction.TransactionType.EXPENSE,
            amount="100.00",
            currency="USD",
        )
        mock_generate.return_value = "the AI could say literally anything here"

        response = authed_client(user).post(URL, {})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["insight"] == "the AI could say literally anything here"
        comparison = {row["category"]: row for row in data["facts"]["category_comparison"]}
        assert comparison["Dining"]["this_month"] == "100.00"

    @patch("apps.ai.llm.generate")
    def test_only_includes_requesting_users_data(self, mock_generate):
        user = UserFactory()
        other = UserFactory()
        other_account = AccountFactory(user=other, currency="USD")
        TransactionFactory(
            user=other,
            account=other_account,
            category=CategoryFactory(user=other, type="expense", name="Secret"),
            type=Transaction.TransactionType.EXPENSE,
            amount="999.00",
            currency="USD",
        )
        mock_generate.return_value = "insight"

        response = authed_client(user).post(URL, {})

        categories = {row["category"] for row in response.data["data"]["facts"]["category_comparison"]}
        assert "Secret" not in categories

    @patch("apps.ai.llm.generate")
    def test_records_usage(self, mock_generate):
        user = UserFactory()
        mock_generate.return_value = "insight"

        authed_client(user).post(URL, {})

        assert AIUsageLog.objects.filter(user=user, endpoint="analyze").count() == 1

    def test_requires_authentication(self):
        response = APIClient().post(URL, {})

        assert response.status_code == 401
