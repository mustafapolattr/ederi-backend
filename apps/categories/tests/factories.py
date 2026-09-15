import factory

from apps.categories.models import Category
from apps.users.tests.factories import UserFactory


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Category {n}")
    icon = "category"
    color = "#6B7280"
    type = Category.CategoryType.EXPENSE
    is_default = False


class DefaultCategoryFactory(CategoryFactory):
    user = None
    is_default = True
