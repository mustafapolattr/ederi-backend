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
from apps.recurring_payments.services import get_expected_totals_by_currency
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


def _current_month_end(today):
    return today.replace(day=calendar.monthrange(today.year, today.month)[1])


def get_month_end_forecast_by_currency(user):
    """Expected month-end balance (spec §26).

        forecast_balance = current_balance
                            + expected_recurring_income (today..month end)
                            - expected_recurring_expenses (today..month end)

    Deliberately simple and explainable: no historical averaging or ML,
    only the current ledger balance and known recurring payments still due
    this month.
    """
    today = datetime.date.today()
    month_end = _current_month_end(today)

    balances = {row["currency"]: Decimal(row["amount"]) for row in get_total_balance_by_currency(user)}
    expected = get_expected_totals_by_currency(user, today, month_end)

    currencies = set(balances) | set(expected)
    result = []
    for currency in sorted(currencies):
        balance = balances.get(currency, Decimal("0.00"))
        flows = expected.get(currency, {})
        income = flows.get("income", Decimal("0.00"))
        expense = flows.get("expense", Decimal("0.00"))
        result.append({"currency": currency, "forecast_balance": str(balance + income - expense)})
    return result


def get_available_to_spend_by_currency(user):
    """Available-to-spend estimate (spec §25).

        available_to_spend = current_balance
                              + expected_income
                              - expected_recurring_expenses
                              - planned_budget_commitments
                              - goal_contributions

    A recurring expense whose category already has an active budget this
    period is left out of expected_recurring_expenses: the budget's
    remaining amount (planned_budget_commitments) already reserves spending
    room for that category, so subtracting the recurring expense on top
    would double count it.
    """
    today = datetime.date.today()
    month_end = _current_month_end(today)

    active_budgets = Budget.objects.filter(user=user, start_date__lte=today, end_date__gte=today)
    budgeted_category_ids = frozenset(active_budgets.values_list("category_id", flat=True))

    balances = {row["currency"]: Decimal(row["amount"]) for row in get_total_balance_by_currency(user)}
    expected = get_expected_totals_by_currency(
        user, today, month_end, exclude_expense_category_ids=budgeted_category_ids
    )

    budget_commitments = {}
    for budget in active_budgets:
        remaining = get_budget_remaining(budget)
        if remaining > 0:
            budget_commitments[budget.currency] = budget_commitments.get(budget.currency, Decimal("0.00")) + remaining

    goal_commitments = {}
    for goal in Goal.objects.filter(user=user):
        contribution = get_required_monthly_contribution(goal)
        goal_commitments[goal.currency] = goal_commitments.get(goal.currency, Decimal("0.00")) + contribution

    currencies = set(balances) | set(expected) | set(budget_commitments) | set(goal_commitments)
    result = []
    for currency in sorted(currencies):
        balance = balances.get(currency, Decimal("0.00"))
        flows = expected.get(currency, {})
        income = flows.get("income", Decimal("0.00"))
        expense = flows.get("expense", Decimal("0.00"))
        budgets_amount = budget_commitments.get(currency, Decimal("0.00"))
        goals_amount = goal_commitments.get(currency, Decimal("0.00"))
        result.append(
            {
                "currency": currency,
                "available_to_spend": str(balance + income - expense - budgets_amount - goals_amount),
            }
        )
    return result


def get_dashboard_data(user):
    return {
        "total_balance": get_total_balance_by_currency(user),
        "this_month": get_this_month_by_currency(user),
        "budgets": get_budget_statuses(user),
        "goals": get_goal_progress(user),
        "forecast": get_month_end_forecast_by_currency(user),
        "available_to_spend": get_available_to_spend_by_currency(user),
    }
