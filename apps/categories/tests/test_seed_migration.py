import pytest

from apps.categories.models import Category


@pytest.mark.django_db
class TestDefaultCategorySeed:
    def test_twelve_default_categories_exist(self):
        defaults = Category.objects.filter(user__isnull=True, is_default=True)

        assert defaults.count() == 12
        assert set(defaults.values_list("name", flat=True)) == {
            "Food",
            "Transport",
            "Housing",
            "Bills",
            "Shopping",
            "Entertainment",
            "Health",
            "Education",
            "Travel",
            "Subscriptions",
            "Personal",
            "Other",
        }

    def test_default_categories_are_expense_type(self):
        assert not Category.objects.filter(user__isnull=True, is_default=True).exclude(type="expense").exists()
