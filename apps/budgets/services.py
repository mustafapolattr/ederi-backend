"""Deterministic budget math (spec §22).

budget_remaining = budget_amount - actual_expenses, where actual_expenses is
the sum of the budget's own category's EXPENSE transactions within its
period. Refunds are not netted out in Phase 3.
"""

from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from apps.transactions.models import Transaction

MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


def get_budget_spent(budget) -> Decimal:
    return Transaction.objects.filter(
        user_id=budget.user_id,
        category_id=budget.category_id,
        type=Transaction.TransactionType.EXPENSE,
        transaction_date__gte=budget.start_date,
        transaction_date__lte=budget.end_date,
    ).aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=MONEY_FIELD))["total"]


def get_budget_remaining(budget) -> Decimal:
    # budget.amount may still be a plain str/int if the instance was just
    # constructed in memory (Django doesn't coerce a DecimalField's value on
    # assignment, only on save) — Decimal() is a no-op if it's already one.
    amount = Decimal(str(budget.amount))
    return amount - get_budget_spent(budget)
