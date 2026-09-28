from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.users.tests.factories import UserFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/scenario/"


@pytest.mark.django_db
class TestScenario:
    @patch("apps.ai.llm.generate")
    def test_projected_balance_is_computed_by_backend_not_llm(self, mock_generate):
        user = UserFactory()
        AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        mock_generate.return_value = "this text is irrelevant to the math"

        response = authed_client(user).post(URL, {"amount": "500.00", "currency": "USD"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["current_available_to_spend"] == "1000.00"
        assert data["projected_available_to_spend"] == "500.00"
        assert data["explanation"] == "this text is irrelevant to the math"

    @patch("apps.ai.llm.generate")
    def test_unknown_currency_defaults_to_zero_balance(self, mock_generate):
        user = UserFactory()
        AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        mock_generate.return_value = "ok"

        response = authed_client(user).post(URL, {"amount": "50.00", "currency": "EUR"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["current_available_to_spend"] == "0.00"
        assert data["projected_available_to_spend"] == "-50.00"

    def test_requires_authentication(self):
        response = APIClient().post(URL, {"amount": "50.00", "currency": "USD"})

        assert response.status_code == 401
