from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token_generator


def _uid_for(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def send_verification_email(user):
    uid = _uid_for(user)
    token = email_verification_token_generator.make_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/verify-email?uid={uid}&token={token}"
    send_mail(
        subject="Verify your Ederi account",
        message=f"Welcome to Ederi. Verify your email address: {link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    uid = _uid_for(user)
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Reset your Ederi password",
        message=f"Reset your password: {link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
