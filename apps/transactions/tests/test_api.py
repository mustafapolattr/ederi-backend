import datetime

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.categories.tests.factories import CategoryFactory
from apps.transactions.models import Transaction
from apps.users.tests.factories import UserFactory

from .factories import TransactionFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestTransactionCreate:
    def test_create_expense(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        category = CategoryFactory(user=user, type="expense")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "category": str(category.id),
                "type": "expense",
                "amount": "100.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 201
        assert Transaction.objects.get(id=response.data["id"]).source == "manual"

    def test_create_transfer_requires_to_account(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "type": "transfer",
                "amount": "50.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "to_account"

    def test_create_transfer_to_same_account_rejected(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "to_account": str(account.id),
                "type": "transfer",
                "amount": "50.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400

    def test_to_account_rejected_for_non_transfer(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        other_account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "to_account": str(other_account.id),
                "type": "expense",
                "amount": "50.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "to_account"

    def test_cannot_use_another_users_account(self):
        user = UserFactory()
        other = UserFactory()
        other_account = AccountFactory(user=other, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(other_account.id),
                "type": "expense",
                "amount": "50.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "account"

    def test_cannot_use_another_users_category(self):
        user = UserFactory()
        other = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        other_category = CategoryFactory(user=other, type="expense")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "category": str(other_category.id),
                "type": "expense",
                "amount": "50.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "category"

    def test_currency_must_match_account(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "type": "expense",
                "amount": "50.00",
                "currency": "EUR",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "currency"

    def test_negative_amount_rejected_for_expense(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "type": "expense",
                "amount": "-10.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400

    def test_zero_amount_rejected_for_adjustment(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "type": "adjustment",
                "amount": "0.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 400

    def test_negative_amount_allowed_for_adjustment(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/transactions/",
            {
                "account": str(account.id),
                "type": "adjustment",
                "amount": "-25.00",
                "currency": "USD",
                "transaction_date": str(datetime.date.today()),
            },
        )

        assert response.status_code == 201


@pytest.mark.django_db
class TestTransactionDetail:
    def test_cannot_access_another_users_transaction(self):
        owner = UserFactory()
        attacker = UserFactory()
        account = AccountFactory(user=owner)
        transaction = TransactionFactory(user=owner, account=account)
        client = authed_client(attacker)

        response = client.get(f"/api/v1/transactions/{transaction.id}/")

        assert response.status_code == 404

    def test_delete_removes_transaction_and_updates_balance(self):
        user = UserFactory()
        account = AccountFactory(user=user, initial_balance="1000.00", currency="USD")
        transaction = TransactionFactory(
            user=user, account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00", currency="USD"
        )
        client = authed_client(user)

        response = client.delete(f"/api/v1/transactions/{transaction.id}/")
        assert response.status_code == 204

        balance_response = client.get(f"/api/v1/accounts/{account.id}/")
        assert balance_response.data["current_balance"] == "1000.00"


@pytest.mark.django_db
class TestTransactionList:
    def test_filters_by_account(self):
        user = UserFactory()
        account_a = AccountFactory(user=user, currency="USD")
        account_b = AccountFactory(user=user, currency="USD")
        TransactionFactory(user=user, account=account_a, currency="USD")
        TransactionFactory(user=user, account=account_b, currency="USD")
        client = authed_client(user)

        response = client.get(f"/api/v1/transactions/?account={account_a.id}")

        assert response.data["count"] == 1

    def test_filters_by_type(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        TransactionFactory(
            user=user, account=account, currency="USD", type=Transaction.TransactionType.INCOME, amount="10.00"
        )
        TransactionFactory(
            user=user, account=account, currency="USD", type=Transaction.TransactionType.EXPENSE, amount="10.00"
        )
        client = authed_client(user)

        response = client.get("/api/v1/transactions/?type=income")

        assert response.data["count"] == 1
