import datetime

import factory

from apps.accounts.tests.factories import AccountFactory
from apps.recurring_payments.models import RecurringPayment


class RecurringPaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecurringPayment

    user = factory.SelfAttribute("account.user")
    account = factory.SubFactory(AccountFactory)
    name = factory.Sequence(lambda n: f"Recurring payment {n}")
    type = RecurringPayment.Type.EXPENSE
    amount = "50.00"
    currency = factory.SelfAttribute("account.currency")
    frequency = RecurringPayment.Frequency.MONTHLY
    next_payment_date = factory.LazyFunction(datetime.date.today)
    category = None
    is_active = True
