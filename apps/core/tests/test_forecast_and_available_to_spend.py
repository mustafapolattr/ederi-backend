import datetime

import pytest

from apps.accounts.tests.factories import AccountFactory
from apps.budgets.tests.factories import BudgetFactory
from apps.categories.tests.factories import CategoryFactory
from apps.core.services import get_available_to_spend_by_currency, get_month_end_forecast_by_currency
from apps.recurring_payments.models import RecurringPayment
from apps.recurring_payments.tests.factories import RecurringPaymentFactory
from apps.users.tests.factories import UserFactory


def _by_currency(rows, key):
    return {row["currency"]: row[key] for row in rows}


@pytest.mark.django_db
class TestMonthEndForecast:
    def test_adds_expected_income_and_subtracts_expected_expenses(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        today = datetime.date.today()
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.INCOME,
            amount="200.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="50.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )

        forecast = _by_currency(get_month_end_forecast_by_currency(user), "forecast_balance")

        assert forecast["USD"] == "1150.00"

    def test_inactive_recurring_payments_are_ignored(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="500.00")
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="100.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date.today(),
            is_active=False,
        )

        forecast = _by_currency(get_month_end_forecast_by_currency(user), "forecast_balance")

        assert forecast["USD"] == "500.00"


@pytest.mark.django_db
class TestAvailableToSpend:
    def test_formula_without_budgets_or_goals(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        today = datetime.date.today()
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.INCOME,
            amount="200.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="50.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )

        available = _by_currency(get_available_to_spend_by_currency(user), "available_to_spend")

        assert available["USD"] == "1150.00"

    def test_subtracts_planned_budget_commitments_and_goal_contributions(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        today = datetime.date.today()
        BudgetFactory(
            user=user,
            category=CategoryFactory(user=user, type="expense"),
            amount="300.00",
            currency="USD",
            start_date=today.replace(day=1),
            end_date=today,
        )

        available = _by_currency(get_available_to_spend_by_currency(user), "available_to_spend")

        assert available["USD"] == "700.00"

    def test_does_not_double_count_a_recurring_expense_already_covered_by_an_active_budget(self):
        """A recurring expense in a category that already has an active
        budget must not also be subtracted on top of the budget's remaining
        amount — the budget already reserves that spending room."""
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        today = datetime.date.today()
        category = CategoryFactory(user=user, type="expense")
        BudgetFactory(
            user=user,
            category=category,
            amount="300.00",
            currency="USD",
            start_date=today.replace(day=1),
            end_date=today,
        )
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="80.00",
            category=category,
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )

        available = _by_currency(get_available_to_spend_by_currency(user), "available_to_spend")

        # 1000 balance - 300 budget commitment. The 80.00 recurring expense
        # in the same (budgeted) category is NOT subtracted a second time.
        assert available["USD"] == "700.00"

    def test_recurring_expense_in_an_unbudgeted_category_is_still_subtracted(self):
        user = UserFactory()
        account = AccountFactory(user=user, currency="USD", initial_balance="1000.00")
        today = datetime.date.today()
        # Budget covers a different category than the recurring expense.
        BudgetFactory(
            user=user,
            category=CategoryFactory(user=user, type="expense"),
            amount="300.00",
            currency="USD",
            start_date=today.replace(day=1),
            end_date=today,
        )
        RecurringPaymentFactory(
            account=account,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="80.00",
            category=CategoryFactory(user=user, type="expense"),
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=today,
        )

        available = _by_currency(get_available_to_spend_by_currency(user), "available_to_spend")

        assert available["USD"] == "620.00"
