import datetime

import factory

from apps.accounts.tests.factories import AccountFactory
from apps.transactions.models import Transaction


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    user = factory.SelfAttribute("account.user")
    account = factory.SubFactory(AccountFactory)
    category = None
    type = Transaction.TransactionType.EXPENSE
    amount = "10.00"
    currency = factory.SelfAttribute("account.currency")
    transaction_date = factory.LazyFunction(datetime.date.today)
