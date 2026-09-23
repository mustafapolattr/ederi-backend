import datetime

import factory

from apps.goals.models import Goal
from apps.users.tests.factories import UserFactory


class GoalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Goal

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Goal {n}")
    goal_type = Goal.GoalType.CUSTOM
    target_amount = "1200.00"
    current_amount = "0.00"
    currency = "USD"
    target_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=365))
