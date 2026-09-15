import pytest
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory

from .factories import CategoryFactory, DefaultCategoryFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestCategoryList:
    def test_list_includes_defaults_and_own_but_not_other_users_custom(self):
        user = UserFactory()
        other = UserFactory()
        CategoryFactory(user=user, name="Mine")
        CategoryFactory(user=other, name="Theirs")
        client = authed_client(user)

        response = client.get("/api/v1/categories/")

        names = {c["name"] for c in response.data["results"]}
        # The 12 spec-defined defaults (seeded by migration) are always visible.
        assert "Food" in names  # a seeded default
        assert "Mine" in names
        assert "Theirs" not in names

    def test_create_always_produces_a_custom_non_default_category(self):
        user = UserFactory()
        client = authed_client(user)

        response = client.post(
            "/api/v1/categories/",
            {"name": "Side hustle", "type": "income", "is_default": True},
        )

        assert response.status_code == 201
        assert response.data["is_default"] is False


@pytest.mark.django_db
class TestCategoryDetail:
    def test_cannot_edit_default_category(self):
        user = UserFactory()
        category = DefaultCategoryFactory(name="Food")
        client = authed_client(user)

        response = client.patch(f"/api/v1/categories/{category.id}/", {"name": "Hacked"})

        assert response.status_code == 403
        category.refresh_from_db()
        assert category.name == "Food"

    def test_cannot_delete_default_category(self):
        user = UserFactory()
        category = DefaultCategoryFactory(name="Food")
        client = authed_client(user)

        response = client.delete(f"/api/v1/categories/{category.id}/")

        assert response.status_code == 403

    def test_can_edit_own_custom_category(self):
        user = UserFactory()
        category = CategoryFactory(user=user, name="Old name")
        client = authed_client(user)

        response = client.patch(f"/api/v1/categories/{category.id}/", {"name": "New name"})

        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == "New name"

    def test_cannot_access_another_users_custom_category(self):
        owner = UserFactory()
        attacker = UserFactory()
        category = CategoryFactory(user=owner)
        client = authed_client(attacker)

        response = client.get(f"/api/v1/categories/{category.id}/")

        assert response.status_code == 404

    def test_cannot_delete_another_users_custom_category(self):
        owner = UserFactory()
        attacker = UserFactory()
        category = CategoryFactory(user=owner)
        client = authed_client(attacker)

        response = client.delete(f"/api/v1/categories/{category.id}/")

        assert response.status_code == 404
