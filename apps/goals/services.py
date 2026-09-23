"""Deterministic goal math (spec §23).

remaining_amount = target_amount - current_amount (floored at 0)
required_monthly_contribution = remaining_amount / remaining_months
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def get_remaining_amount(goal) -> Decimal:
    # target_amount/current_amount may still be a plain str/int if the
    # instance was just constructed in memory (Django doesn't coerce a
    # DecimalField's value on assignment, only on save).
    target_amount = Decimal(str(goal.target_amount))
    current_amount = Decimal(str(goal.current_amount))
    remaining = target_amount - current_amount
    return remaining if remaining > 0 else Decimal("0.00")


def get_remaining_months(goal, today: datetime.date | None = None) -> int:
    """Whole calendar months between today and target_date, ceiled and
    floored to a minimum of 1 while the target date is still ahead.

    0 means the target date has already arrived or passed.
    """
    today = today or datetime.date.today()
    target_date = goal.target_date
    if target_date <= today:
        return 0

    months = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    if target_date.day > today.day:
        months += 1
    return max(months, 1)


def get_required_monthly_contribution(goal, today: datetime.date | None = None) -> Decimal:
    remaining = get_remaining_amount(goal)
    if remaining <= 0:
        return Decimal("0.00")

    months = get_remaining_months(goal, today=today)
    if months <= 0:
        # Target date already reached/passed: the whole remainder is due now.
        return remaining.quantize(CENTS, rounding=ROUND_HALF_UP)
    return (remaining / months).quantize(CENTS, rounding=ROUND_HALF_UP)
