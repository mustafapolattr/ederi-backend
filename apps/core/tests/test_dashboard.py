import datetime

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import AccountFactory
from apps.budgets.tests.factories import BudgetFactory
from apps.categories.tests.factories import CategoryFactory
from apps.goals.tests.factories import GoalFactory
from apps.transactions.models import Transaction
from apps.transactions.tests.factories import TransactionFactory
from apps.users.tests.factories import UserFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _by_currency(rows, key):
    return {row["currency"]: row[key] for row in rows}


@pytest.mark.django_db
class TestDashboard:
    def test_requires_authentication(self):
        client = APIClient()

        response = client.get("/api/v1/dashboard/")

        assert response.status_code == 401

    def test_balances_and_month_totals_are_grouped_by_currency_not_summed_together(self):
        user = UserFactory()
        usd_account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        try_account = AccountFactory(user=user, currency="TRY", initial_balance="5000.00")

        TransactionFactory(
            user=user,
            account=usd_account,
            currency="USD",
            type=Transaction.TransactionType.INCOME,
            amount="300.00",
            transaction_date=datetime.date.today(),
        )
        TransactionFactory(
            user=user,
            account=usd_account,
            currency="USD",
            type=Transaction.TransactionType.EXPENSE,
            amount="100.00",
            transaction_date=datetime.date.today(),
        )
        TransactionFactory(
            user=user,
            account=try_account,
            currency="TRY",
            type=Transaction.TransactionType.EXPENSE,
            amount="2000.00",
            transaction_date=datetime.date.today(),
        )

        client = authed_client(user)
        response = client.get("/api/v1/dashboard/")

        assert response.status_code == 200
        data = response.data["data"]

        total_balance = {row["currency"]: row["amount"] for row in data["total_balance"]}
        assert total_balance == {"USD": "1200.00", "TRY": "3000.00"}

        this_month = {row["currency"]: row for row in data["this_month"]}
        assert this_month["USD"]["income"] == "300.00"
        assert this_month["USD"]["expense"] == "100.00"
        assert this_month["USD"]["saved"] == "200.00"
        assert this_month["TRY"]["income"] == "0.00"
        assert this_month["TRY"]["expense"] == "2000.00"
        assert this_month["TRY"]["saved"] == "-2000.00"

    def test_excludes_last_months_transactions(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="0.00")
        last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1))
        TransactionFactory(
            user=user,
            account=account,
            currency="USD",
            type=Transaction.TransactionType.INCOME,
            amount="500.00",
            transaction_date=last_month,
        )
        client = authed_client(user)

        response = client.get("/api/v1/dashboard/")

        assert response.data["data"]["this_month"] == []

    def test_includes_budgets_active_this_month(self):
        user = UserFactory()
        category = CategoryFactory(user=user, type="expense")
        today = datetime.date.today()
        BudgetFactory(
            user=user,
            category=category,
            amount="500.00",
            currency="USD",
            start_date=today.replace(day=1),
            end_date=today,
        )
        client = authed_client(user)

        response = client.get("/api/v1/dashboard/")

        budgets = response.data["data"]["budgets"]
        assert len(budgets) == 1
        assert budgets[0]["amount"] == "500.00"
        assert budgets[0]["remaining"] == "500.00"

    def test_includes_goal_progress(self):
        user = UserFactory()
        GoalFactory(user=user, target_amount="1000.00", current_amount="400.00")
        client = authed_client(user)

        response = client.get("/api/v1/dashboard/")

        goals = response.data["data"]["goals"]
        assert len(goals) == 1
        assert goals[0]["remaining_amount"] == "600.00"

    def test_includes_forecast_and_available_to_spend(self):
        user = UserFactory()
        AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        client = authed_client(user)

        response = client.get("/api/v1/dashboard/")

        data = response.data["data"]
        assert _by_currency(data["forecast"], "forecast_balance")["USD"] == "1000.00"
        assert _by_currency(data["available_to_spend"], "available_to_spend")["USD"] == "1000.00"
