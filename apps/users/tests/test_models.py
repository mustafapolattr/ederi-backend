import pytest
from django.db import IntegrityError

from apps.users.models import User

from .factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_hashes_password(self):
        user = User.objects.create_user(email="jane@example.com", password="Str0ngPassw0rd!")

        assert user.email == "jane@example.com"
        assert user.password != "Str0ngPassw0rd!"
        assert user.check_password("Str0ngPassw0rd!")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_email_verified is False

    def test_create_superuser_sets_staff_and_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="Str0ngPassw0rd!")

        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.is_email_verified is True

    def test_email_is_unique(self):
        UserFactory(email="dup@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="dup@example.com")

    def test_email_normalized_on_create_user(self):
        user = User.objects.create_user(email="Jane@Example.com", password="Str0ngPassw0rd!")

        assert user.email == "Jane@example.com"
