import datetime

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.users.tests.factories import UserFactory

from .factories import RecurringPaymentFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestRecurringPaymentCreate:
    def test_create_recurring_payment(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/recurring-payments/",
            {
                "name": "Netflix",
                "type": "expense",
                "amount": "15.99",
                "currency": "USD",
                "frequency": "monthly",
                "next_payment_date": str(datetime.date.today() + datetime.timedelta(days=10)),
                "account": str(account.id),
            },
        )

        assert response.status_code == 201
        assert response.data["name"] == "Netflix"

    def test_amount_must_be_positive(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/recurring-payments/",
            {
                "name": "Bad payment",
                "type": "expense",
                "amount": "0.00",
                "currency": "USD",
                "frequency": "monthly",
                "next_payment_date": str(datetime.date.today()),
                "account": str(account.id),
            },
        )

        assert response.status_code == 400

    def test_cannot_use_another_users_account(self):
        user = UserFactory()
        other_account = AccountFactory(user=UserFactory(), currency="USD")
        client = authed_client(user)

        response = client.post(
            "/api/v1/recurring-payments/",
            {
                "name": "Sneaky",
                "type": "expense",
                "amount": "10.00",
                "currency": "USD",
                "frequency": "monthly",
                "next_payment_date": str(datetime.date.today()),
                "account": str(other_account.id),
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestRecurringPaymentDetail:
    def test_cannot_access_another_users_recurring_payment(self):
        owner = UserFactory()
        attacker = UserFactory()
        payment = RecurringPaymentFactory(account=AccountFactory(user=owner))
        client = authed_client(attacker)

        response = client.get(f"/api/v1/recurring-payments/{payment.id}/")

        assert response.status_code == 404

    def test_update_is_active(self):
        user = UserFactory()
        payment = RecurringPaymentFactory(account=AccountFactory(user=user), is_active=True)
        client = authed_client(user)

        response = client.patch(f"/api/v1/recurring-payments/{payment.id}/", {"is_active": False})

        assert response.status_code == 200
        assert response.data["is_active"] is False

    def test_delete_recurring_payment(self):
        user = UserFactory()
        payment = RecurringPaymentFactory(account=AccountFactory(user=user))
        client = authed_client(user)

        response = client.delete(f"/api/v1/recurring-payments/{payment.id}/")

        assert response.status_code == 204


@pytest.mark.django_db
class TestRecurringPaymentList:
    def test_list_only_returns_own_recurring_payments(self):
        user = UserFactory()
        other = UserFactory()
        RecurringPaymentFactory(account=AccountFactory(user=user))
        RecurringPaymentFactory(account=AccountFactory(user=other))
        client = authed_client(user)

        response = client.get("/api/v1/recurring-payments/")

        assert response.data["count"] == 1
