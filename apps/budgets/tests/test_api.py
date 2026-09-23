import pytest
from rest_framework.test import APIClient

from apps.categories.tests.factories import CategoryFactory
from apps.users.tests.factories import UserFactory

from .factories import BudgetFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestBudgetCreate:
    def test_create_budget(self):
        user = UserFactory()
        category = CategoryFactory(user=user, type="expense")
        client = authed_client(user)

        response = client.post(
            "/api/v1/budgets/",
            {
                "category": str(category.id),
                "amount": "300.00",
                "currency": "USD",
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
            },
        )

        assert response.status_code == 201
        assert response.data["remaining"] == "300.00"
        assert response.data["period"] == "monthly"

    def test_cannot_use_another_users_category(self):
        user = UserFactory()
        other = UserFactory()
        other_category = CategoryFactory(user=other, type="expense")
        client = authed_client(user)

        response = client.post(
            "/api/v1/budgets/",
            {
                "category": str(other_category.id),
                "amount": "300.00",
                "currency": "USD",
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "category"

    def test_end_date_before_start_date_rejected(self):
        user = UserFactory()
        category = CategoryFactory(user=user, type="expense")
        client = authed_client(user)

        response = client.post(
            "/api/v1/budgets/",
            {
                "category": str(category.id),
                "amount": "300.00",
                "currency": "USD",
                "start_date": "2026-09-30",
                "end_date": "2026-09-01",
            },
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "end_date"

    def test_duplicate_budget_for_same_category_and_period_rejected(self):
        user = UserFactory()
        category = CategoryFactory(user=user, type="expense")
        BudgetFactory(user=user, category=category, start_date="2026-09-01", end_date="2026-09-30")
        client = authed_client(user)

        response = client.post(
            "/api/v1/budgets/",
            {
                "category": str(category.id),
                "amount": "300.00",
                "currency": "USD",
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestBudgetDetail:
    def test_cannot_access_another_users_budget(self):
        owner = UserFactory()
        attacker = UserFactory()
        budget = BudgetFactory(user=owner)
        client = authed_client(attacker)

        response = client.get(f"/api/v1/budgets/{budget.id}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestBudgetList:
    def test_list_only_returns_own_budgets(self):
        user = UserFactory()
        other = UserFactory()
        BudgetFactory(user=user)
        BudgetFactory(user=other)
        client = authed_client(user)

        response = client.get("/api/v1/budgets/")

        assert response.data["count"] == 1

    def test_filters_by_month(self):
        user = UserFactory()
        BudgetFactory(user=user, start_date="2026-09-01", end_date="2026-09-30")
        BudgetFactory(user=user, category=CategoryFactory(user=user, type="expense"), start_date="2026-10-01", end_date="2026-10-31")
        client = authed_client(user)

        response = client.get("/api/v1/budgets/?month=2026-09")

        assert response.data["count"] == 1
