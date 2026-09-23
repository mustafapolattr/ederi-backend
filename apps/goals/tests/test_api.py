import datetime

import pytest
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory

from .factories import GoalFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestGoalCreate:
    def test_create_goal(self):
        user = UserFactory()
        client = authed_client(user)

        response = client.post(
            "/api/v1/goals/",
            {
                "name": "Emergency fund",
                "goal_type": "emergency_fund",
                "target_amount": "1200.00",
                "current_amount": "0.00",
                "currency": "USD",
                "target_date": str(datetime.date.today() + datetime.timedelta(days=365)),
            },
        )

        assert response.status_code == 201
        assert response.data["remaining_amount"] == "1200.00"

    def test_target_amount_must_be_positive(self):
        user = UserFactory()
        client = authed_client(user)

        response = client.post(
            "/api/v1/goals/",
            {
                "name": "Bad goal",
                "target_amount": "0.00",
                "currency": "USD",
                "target_date": str(datetime.date.today() + datetime.timedelta(days=30)),
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestGoalDetail:
    def test_cannot_access_another_users_goal(self):
        owner = UserFactory()
        attacker = UserFactory()
        goal = GoalFactory(user=owner)
        client = authed_client(attacker)

        response = client.get(f"/api/v1/goals/{goal.id}/")

        assert response.status_code == 404

    def test_update_current_amount_updates_progress(self):
        user = UserFactory()
        goal = GoalFactory(user=user, target_amount="1000.00", current_amount="0.00")
        client = authed_client(user)

        response = client.patch(f"/api/v1/goals/{goal.id}/", {"current_amount": "250.00"})

        assert response.status_code == 200
        assert response.data["current_amount"] == "250.00"
        assert response.data["remaining_amount"] == "750.00"


@pytest.mark.django_db
class TestGoalList:
    def test_list_only_returns_own_goals(self):
        user = UserFactory()
        other = UserFactory()
        GoalFactory(user=user)
        GoalFactory(user=other)
        client = authed_client(user)

        response = client.get("/api/v1/goals/")

        assert response.data["count"] == 1
