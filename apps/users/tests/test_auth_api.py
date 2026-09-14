from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.users.models import User

from .factories import UserFactory


def _link_params(email_body):
    link = email_body.strip().split(": ")[-1]
    query = parse_qs(urlparse(link).query)
    return query["uid"][0], query["token"][0]


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_user_and_sends_verification_email(self):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/register/",
            {"email": "new@example.com", "password": "Str0ngPassw0rd!", "first_name": "New"},
        )

        assert response.status_code == 201
        user = User.objects.get(email="new@example.com")
        assert user.check_password("Str0ngPassw0rd!")
        assert user.is_email_verified is False
        assert "password" not in response.data
        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_register_rejects_duplicate_email(self):
        UserFactory(email="taken@example.com")
        client = APIClient()

        response = client.post(
            "/api/v1/auth/register/",
            {"email": "taken@example.com", "password": "Str0ngPassw0rd!"},
        )

        assert response.status_code == 400
        assert response.data["success"] is False
        assert response.data["error"]["field"] == "email"

    def test_register_rejects_weak_password(self):
        client = APIClient()

        response = client.post(
            "/api/v1/auth/register/",
            {"email": "weak@example.com", "password": "12345"},
        )

        assert response.status_code == 400
        assert response.data["error"]["field"] == "password"


@pytest.mark.django_db
class TestLogin:
    def test_login_returns_access_and_refresh_tokens(self):
        UserFactory(email="login@example.com", password="Str0ngPassw0rd!")
        client = APIClient()

        response = client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "Str0ngPassw0rd!"},
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_rejects_wrong_password(self):
        UserFactory(email="login2@example.com", password="Str0ngPassw0rd!")
        client = APIClient()

        response = client.post(
            "/api/v1/auth/login/",
            {"email": "login2@example.com", "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.data["success"] is False


@pytest.mark.django_db
class TestProfile:
    def test_profile_requires_authentication(self):
        client = APIClient()

        response = client.get("/api/v1/auth/profile/")

        assert response.status_code == 401

    def test_profile_get_and_patch(self):
        user = UserFactory(email="profile@example.com", password="Str0ngPassw0rd!")
        client = APIClient()
        client.force_authenticate(user=user)

        get_response = client.get("/api/v1/auth/profile/")
        assert get_response.status_code == 200
        assert get_response.data["email"] == "profile@example.com"

        patch_response = client.patch("/api/v1/auth/profile/", {"first_name": "Updated"})
        assert patch_response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_profile_cannot_change_email(self):
        user = UserFactory(email="immutable@example.com", password="Str0ngPassw0rd!")
        client = APIClient()
        client.force_authenticate(user=user)

        client.patch("/api/v1/auth/profile/", {"email": "changed@example.com"})

        user.refresh_from_db()
        assert user.email == "immutable@example.com"


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self):
        UserFactory(email="logout@example.com", password="Str0ngPassw0rd!")
        client = APIClient()
        login_response = client.post(
            "/api/v1/auth/login/",
            {"email": "logout@example.com", "password": "Str0ngPassw0rd!"},
        )
        refresh = login_response.data["refresh"]

        logout_response = client.post("/api/v1/auth/logout/", {"refresh": refresh})
        assert logout_response.status_code == 204

        refresh_response = client.post("/api/v1/auth/login/refresh/", {"refresh": refresh})
        assert refresh_response.status_code == 401

    def test_logout_requires_refresh_token(self):
        client = APIClient()

        response = client.post("/api/v1/auth/logout/", {})

        assert response.status_code == 400


@pytest.mark.django_db
class TestPasswordReset:
    def test_password_reset_flow_end_to_end(self):
        UserFactory(email="reset@example.com", password="OldPassw0rd!")
        client = APIClient()

        request_response = client.post("/api/v1/auth/password-reset/", {"email": "reset@example.com"})
        assert request_response.status_code == 200
        assert len(mail.outbox) == 1

        uid, token = _link_params(mail.outbox[0].body)
        confirm_response = client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "NewPassw0rd!"},
        )
        assert confirm_response.status_code == 200

        login_response = client.post(
            "/api/v1/auth/login/",
            {"email": "reset@example.com", "password": "NewPassw0rd!"},
        )
        assert login_response.status_code == 200

    def test_password_reset_does_not_leak_unknown_email(self):
        client = APIClient()

        response = client.post("/api/v1/auth/password-reset/", {"email": "unknown@example.com"})

        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_password_reset_confirm_rejects_invalid_token(self):
        user = UserFactory(email="badtoken@example.com", password="Str0ngPassw0rd!")
        client = APIClient()
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": "not-a-real-token", "new_password": "NewPassw0rd!"},
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestEmailVerification:
    def test_email_verification_flow_end_to_end(self):
        user = UserFactory(email="verify@example.com", password="Str0ngPassw0rd!")
        client = APIClient()
        client.force_authenticate(user=user)

        resend_response = client.post("/api/v1/auth/email/resend/")
        assert resend_response.status_code == 200
        assert len(mail.outbox) == 1

        uid, token = _link_params(mail.outbox[0].body)
        confirm_response = APIClient().post("/api/v1/auth/email/verify/", {"uid": uid, "token": token})
        assert confirm_response.status_code == 200

        user.refresh_from_db()
        assert user.is_email_verified is True

    def test_email_verification_rejects_invalid_token(self):
        user = UserFactory(email="badverify@example.com", password="Str0ngPassw0rd!")
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        client = APIClient()

        response = client.post("/api/v1/auth/email/verify/", {"uid": uid, "token": "invalid"})

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.is_email_verified is False
