import datetime
from decimal import Decimal

import pytest

from apps.accounts.tests.factories import AccountFactory
from apps.budgets.services import get_budget_remaining, get_budget_spent
from apps.categories.tests.factories import CategoryFactory
from apps.transactions.models import Transaction
from apps.transactions.tests.factories import TransactionFactory

from .factories import BudgetFactory


@pytest.mark.django_db
class TestBudgetSpentAndRemaining:
    def test_no_expenses_yet(self):
        budget = BudgetFactory(amount="500.00")

        assert get_budget_spent(budget) == Decimal("0.00")
        assert get_budget_remaining(budget) == Decimal("500.00")

    def test_partial_expense_reduces_remaining(self):
        budget = BudgetFactory(amount="500.00")
        account = AccountFactory(user=budget.user, currency=budget.currency)
        TransactionFactory(
            user=budget.user,
            account=account,
            category=budget.category,
            type=Transaction.TransactionType.EXPENSE,
            amount="120.00",
            currency=budget.currency,
            transaction_date=budget.start_date,
        )

        assert get_budget_spent(budget) == Decimal("120.00")
        assert get_budget_remaining(budget) == Decimal("380.00")

    def test_expenses_over_budget_amount_give_negative_remaining(self):
        budget = BudgetFactory(amount="100.00")
        account = AccountFactory(user=budget.user, currency=budget.currency)
        TransactionFactory(
            user=budget.user,
            account=account,
            category=budget.category,
            type=Transaction.TransactionType.EXPENSE,
            amount="150.00",
            currency=budget.currency,
            transaction_date=budget.start_date,
        )

        assert get_budget_remaining(budget) == Decimal("-50.00")

    def test_only_expense_type_counts_against_budget(self):
        budget = BudgetFactory(amount="500.00")
        account = AccountFactory(user=budget.user, currency=budget.currency)
        for type_ in [
            Transaction.TransactionType.INCOME,
            Transaction.TransactionType.REFUND,
            Transaction.TransactionType.ADJUSTMENT,
            Transaction.TransactionType.TRANSFER,
        ]:
            TransactionFactory(
                user=budget.user,
                account=account,
                category=budget.category,
                type=type_,
                amount="50.00",
                currency=budget.currency,
                transaction_date=budget.start_date,
            )

        assert get_budget_spent(budget) == Decimal("0.00")

    def test_ignores_expenses_outside_the_budget_period(self):
        budget = BudgetFactory(amount="500.00")
        account = AccountFactory(user=budget.user, currency=budget.currency)
        TransactionFactory(
            user=budget.user,
            account=account,
            category=budget.category,
            type=Transaction.TransactionType.EXPENSE,
            amount="90.00",
            currency=budget.currency,
            transaction_date=budget.end_date + datetime.timedelta(days=1),
        )

        assert get_budget_spent(budget) == Decimal("0.00")

    def test_ignores_expenses_in_a_different_category(self):
        budget = BudgetFactory(amount="500.00")
        other_category = CategoryFactory(user=budget.user, type="expense")
        account = AccountFactory(user=budget.user, currency=budget.currency)
        TransactionFactory(
            user=budget.user,
            account=account,
            category=other_category,
            type=Transaction.TransactionType.EXPENSE,
            amount="90.00",
            currency=budget.currency,
            transaction_date=budget.start_date,
        )

        assert get_budget_spent(budget) == Decimal("0.00")
