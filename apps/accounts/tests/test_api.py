from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.transactions.models import Transaction
from apps.transactions.tests.factories import TransactionFactory
from apps.users.tests.factories import UserFactory

from .factories import AccountFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAccountList:
    def test_create_account(self):
        user = UserFactory()
        client = authed_client(user)

        response = client.post(
            "/api/v1/accounts/",
            {"name": "Main bank", "type": "bank", "currency": "USD", "initial_balance": "1000.00"},
        )

        assert response.status_code == 201
        assert response.data["current_balance"] == "1000.00"
        assert response.data["is_active"] is True

    def test_list_only_returns_own_accounts(self):
        user = UserFactory()
        other = UserFactory()
        AccountFactory(user=user)
        AccountFactory(user=other)
        client = authed_client(user)

        response = client.get("/api/v1/accounts/")

        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_requires_authentication(self):
        client = APIClient()

        response = client.get("/api/v1/accounts/")

        assert response.status_code == 401


@pytest.mark.django_db
class TestAccountDetail:
    def test_cannot_access_another_users_account(self):
        owner = UserFactory()
        attacker = UserFactory()
        account = AccountFactory(user=owner)
        client = authed_client(attacker)

        response = client.get(f"/api/v1/accounts/{account.id}/")

        assert response.status_code == 404

    def test_cannot_update_another_users_account(self):
        owner = UserFactory()
        attacker = UserFactory()
        account = AccountFactory(user=owner)
        client = authed_client(attacker)

        response = client.patch(f"/api/v1/accounts/{account.id}/", {"name": "Hacked"})

        assert response.status_code == 404
        account.refresh_from_db()
        assert account.name != "Hacked"

    def test_currency_and_initial_balance_are_immutable_after_create(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="100.00")
        client = authed_client(user)

        response = client.patch(
            f"/api/v1/accounts/{account.id}/",
            {"currency": "EUR", "initial_balance": "999.00", "name": "Renamed"},
        )

        assert response.status_code == 200
        account.refresh_from_db()
        assert account.currency == "USD"
        assert account.initial_balance == Decimal("100.00")
        assert account.name == "Renamed"

    def test_delete_soft_deletes_and_keeps_transaction_history(self):
        user = UserFactory()
        account = AccountFactory(user=user, initial_balance="1000.00")
        TransactionFactory(user=user, account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00")
        client = authed_client(user)

        response = client.delete(f"/api/v1/accounts/{account.id}/")

        assert response.status_code == 204
        account.refresh_from_db()
        assert account.is_active is False
        assert Transaction.objects.filter(account=account).count() == 1

    def test_list_excludes_inactive_by_default(self):
        user = UserFactory()
        AccountFactory(user=user, is_active=False)
        AccountFactory(user=user, is_active=True)
        client = authed_client(user)

        response = client.get("/api/v1/accounts/")

        assert response.data["count"] == 1

    def test_list_includes_inactive_when_requested(self):
        user = UserFactory()
        AccountFactory(user=user, is_active=False)
        AccountFactory(user=user, is_active=True)
        client = authed_client(user)

        response = client.get("/api/v1/accounts/?include_inactive=true")

        assert response.data["count"] == 2

    def test_current_balance_reflects_transactions(self):
        user = UserFactory()
        account = AccountFactory(user=user, initial_balance="1000.00")
        TransactionFactory(user=user, account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00")
        client = authed_client(user)

        response = client.get(f"/api/v1/accounts/{account.id}/")

        assert response.data["current_balance"] == "900.00"
