import datetime
from decimal import Decimal

import pytest

from apps.accounts.tests.factories import AccountFactory
from apps.categories.tests.factories import CategoryFactory
from apps.recurring_payments.models import RecurringPayment
from apps.recurring_payments.services import get_expected_totals_by_currency, get_occurrences_in_range

from .factories import RecurringPaymentFactory


@pytest.mark.django_db
class TestGetOccurrencesInRange:
    def test_weekly_steps_by_seven_days(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.WEEKLY,
            next_payment_date=datetime.date(2026, 9, 1),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 9, 1), datetime.date(2026, 9, 22))

        assert occurrences == [
            datetime.date(2026, 9, 1),
            datetime.date(2026, 9, 8),
            datetime.date(2026, 9, 15),
            datetime.date(2026, 9, 22),
        ]

    def test_monthly_clamps_to_end_of_shorter_month(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date(2026, 1, 31),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 1, 1), datetime.date(2026, 3, 31))

        assert occurrences == [
            datetime.date(2026, 1, 31),
            datetime.date(2026, 2, 28),
            datetime.date(2026, 3, 28),
        ]

    def test_quarterly_steps_by_three_months(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.QUARTERLY,
            next_payment_date=datetime.date(2026, 1, 15),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))

        assert occurrences == [
            datetime.date(2026, 1, 15),
            datetime.date(2026, 4, 15),
            datetime.date(2026, 7, 15),
            datetime.date(2026, 10, 15),
        ]

    def test_yearly_steps_by_twelve_months(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.YEARLY,
            next_payment_date=datetime.date(2026, 3, 1),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 1, 1), datetime.date(2028, 12, 31))

        assert occurrences == [
            datetime.date(2026, 3, 1),
            datetime.date(2027, 3, 1),
            datetime.date(2028, 3, 1),
        ]

    def test_next_payment_date_before_window_rolls_forward_into_it(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.WEEKLY,
            next_payment_date=datetime.date(2026, 9, 1),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 9, 20), datetime.date(2026, 9, 22))

        assert occurrences == [datetime.date(2026, 9, 22)]

    def test_next_payment_date_after_window_returns_nothing(self):
        payment = RecurringPaymentFactory(
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date(2026, 12, 1),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 9, 1), datetime.date(2026, 9, 30))

        assert occurrences == []

    def test_inactive_payment_has_no_occurrences(self):
        payment = RecurringPaymentFactory(
            is_active=False,
            frequency=RecurringPayment.Frequency.WEEKLY,
            next_payment_date=datetime.date(2026, 9, 1),
        )

        occurrences = get_occurrences_in_range(payment, datetime.date(2026, 9, 1), datetime.date(2026, 9, 30))

        assert occurrences == []


@pytest.mark.django_db
class TestGetExpectedTotalsByCurrency:
    def test_sums_income_and_expense_separately_per_currency(self):
        account_usd = AccountFactory(currency="USD")
        user = account_usd.user
        RecurringPaymentFactory(
            account=account_usd,
            currency="USD",
            type=RecurringPayment.Type.INCOME,
            amount="1000.00",
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date(2026, 9, 15),
        )
        RecurringPaymentFactory(
            account=account_usd,
            currency="USD",
            type=RecurringPayment.Type.EXPENSE,
            amount="200.00",
            frequency=RecurringPayment.Frequency.WEEKLY,
            next_payment_date=datetime.date(2026, 9, 1),
        )

        totals = get_expected_totals_by_currency(user, datetime.date(2026, 9, 1), datetime.date(2026, 9, 30))

        assert totals["USD"]["income"] == Decimal("1000.00")
        # 5 weekly occurrences of 200.00 between Sep 1 and Sep 30 inclusive
        # (1, 8, 15, 22, 29).
        assert totals["USD"]["expense"] == Decimal("1000.00")

    def test_excludes_expense_payments_in_the_given_category_set(self):
        payment = RecurringPaymentFactory(
            type=RecurringPayment.Type.EXPENSE,
            amount="75.00",
            category=CategoryFactory(),
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date(2026, 9, 10),
        )

        totals = get_expected_totals_by_currency(
            payment.user,
            datetime.date(2026, 9, 1),
            datetime.date(2026, 9, 30),
            exclude_expense_category_ids=frozenset([payment.category_id]),
        )

        assert totals == {}

    def test_does_not_exclude_income_payments_sharing_the_category(self):
        category = CategoryFactory()
        payment = RecurringPaymentFactory(
            type=RecurringPayment.Type.INCOME,
            amount="75.00",
            category=category,
            frequency=RecurringPayment.Frequency.MONTHLY,
            next_payment_date=datetime.date(2026, 9, 10),
        )

        totals = get_expected_totals_by_currency(
            payment.user,
            datetime.date(2026, 9, 1),
            datetime.date(2026, 9, 30),
            exclude_expense_category_ids=frozenset([category.id]),
        )

        assert totals[payment.currency]["income"] == Decimal("75.00")
