import factory

from apps.accounts.models import Account
from apps.users.tests.factories import UserFactory


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Account {n}")
    type = Account.AccountType.BANK
    currency = "USD"
    initial_balance = "0.00"
    is_active = True
