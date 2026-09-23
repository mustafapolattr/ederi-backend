import datetime
from decimal import Decimal

import pytest

from apps.goals.services import get_remaining_amount, get_remaining_months, get_required_monthly_contribution

from .factories import GoalFactory


@pytest.mark.django_db
class TestRemainingAmount:
    def test_remaining_amount_subtracts_current_from_target(self):
        goal = GoalFactory(target_amount="1000.00", current_amount="400.00")

        assert get_remaining_amount(goal) == Decimal("600.00")

    def test_remaining_amount_never_goes_negative(self):
        goal = GoalFactory(target_amount="1000.00", current_amount="1500.00")

        assert get_remaining_amount(goal) == Decimal("0.00")


@pytest.mark.django_db
class TestRemainingMonths:
    def test_exact_month_boundary(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_date=datetime.date(2026, 12, 23))

        assert get_remaining_months(goal, today=today) == 3

    def test_partial_month_rounds_up(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_date=datetime.date(2026, 11, 30))

        assert get_remaining_months(goal, today=today) == 3

    def test_same_month_still_ahead_counts_as_one(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_date=datetime.date(2026, 9, 25))

        assert get_remaining_months(goal, today=today) == 1

    def test_target_date_today_is_zero_months(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_date=today)

        assert get_remaining_months(goal, today=today) == 0

    def test_target_date_in_the_past_is_zero_months(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_date=datetime.date(2026, 1, 1))

        assert get_remaining_months(goal, today=today) == 0


@pytest.mark.django_db
class TestRequiredMonthlyContribution:
    def test_splits_remaining_amount_evenly_across_remaining_months(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_amount="1200.00", current_amount="0.00", target_date=datetime.date(2026, 12, 23))

        assert get_required_monthly_contribution(goal, today=today) == Decimal("400.00")

    def test_rounds_to_the_nearest_cent(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_amount="1000.00", current_amount="0.00", target_date=datetime.date(2026, 12, 23))

        assert get_required_monthly_contribution(goal, today=today) == Decimal("333.33")

    def test_goal_already_achieved_requires_nothing_more(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_amount="1000.00", current_amount="1000.00", target_date=datetime.date(2026, 12, 23))

        assert get_required_monthly_contribution(goal, today=today) == Decimal("0.00")

    def test_overdue_goal_requires_the_full_remaining_amount_now(self):
        today = datetime.date(2026, 9, 23)
        goal = GoalFactory(target_amount="1000.00", current_amount="200.00", target_date=datetime.date(2026, 1, 1))

        assert get_required_monthly_contribution(goal, today=today) == Decimal("800.00")
