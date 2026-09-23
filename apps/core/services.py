"""Dashboard aggregation (spec §14).

Money is grouped by currency rather than summed across currencies — there is
no FX conversion in the MVP (spec §35), so a single number would silently mix
currencies.
"""

import calendar
import datetime
from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from apps.accounts.models import Account
from apps.budgets.models import Budget
from apps.budgets.services import get_budget_remaining, get_budget_spent
from apps.goals.models import Goal
from apps.goals.services import get_remaining_amount, get_required_monthly_contribution
from apps.transactions.models import Transaction
from apps.transactions.services import annotate_balances

MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


def get_total_balance_by_currency(user):
    accounts = annotate_balances(Account.objects.filter(user=user, is_active=True))
    totals = {}
    for account in accounts:
        totals[account.currency] = totals.get(account.currency, Decimal("0")) + account.current_balance
    return [{"currency": currency, "amount": str(amount)} for currency, amount in sorted(totals.items())]


def get_this_month_by_currency(user):
    today = datetime.date.today()
    start = today.replace(day=1)
    end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    rows = (
        Transaction.objects.filter(
            user=user,
            transaction_date__gte=start,
            transaction_date__lte=end,
            type__in=[Transaction.TransactionType.INCOME, Transaction.TransactionType.EXPENSE],
        )
        .values("currency", "type")
        .annotate(total=Coalesce(Sum("amount"), Value(0), output_field=MONEY_FIELD))
    )

    totals = {}
    for row in rows:
        entry = totals.setdefault(row["currency"], {"income": Decimal("0.00"), "expense": Decimal("0.00")})
        entry[row["type"]] = row["total"]

    return [
        {
            "currency": currency,
            "income": str(values["income"]),
            "expense": str(values["expense"]),
            "saved": str(values["income"] - values["expense"]),
        }
        for currency, values in sorted(totals.items())
    ]


def get_budget_statuses(user):
    today = datetime.date.today()
    budgets = Budget.objects.filter(user=user, start_date__lte=today, end_date__gte=today).select_related("category")
    return [
        {
            "id": str(budget.id),
            "category": budget.category.name,
            "amount": str(budget.amount),
            "currency": budget.currency,
            "spent": str(get_budget_spent(budget)),
            "remaining": str(get_budget_remaining(budget)),
        }
        for budget in budgets
    ]


def get_goal_progress(user):
    goals = Goal.objects.filter(user=user)
    return [
        {
            "id": str(goal.id),
            "name": goal.name,
            "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "currency": goal.currency,
            "target_date": goal.target_date.isoformat(),
            "remaining_amount": str(get_remaining_amount(goal)),
            "required_monthly_contribution": str(get_required_monthly_contribution(goal)),
        }
        for goal in goals
    ]


def get_dashboard_data(user):
    return {
        "total_balance": get_total_balance_by_currency(user),
        "this_month": get_this_month_by_currency(user),
        "budgets": get_budget_statuses(user),
        "goals": get_goal_progress(user),
    }
