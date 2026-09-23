import datetime

import factory

from apps.categories.tests.factories import CategoryFactory
from apps.budgets.models import Budget
from apps.users.tests.factories import UserFactory


def _first_of_month(today=None):
    today = today or datetime.date.today()
    return today.replace(day=1)


def _last_of_month(today=None):
    today = today or datetime.date.today()
    next_month = today.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


class BudgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Budget

    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    amount = "500.00"
    currency = "USD"
    start_date = factory.LazyFunction(_first_of_month)
    end_date = factory.LazyFunction(_last_of_month)
