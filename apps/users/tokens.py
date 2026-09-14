from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Same HMAC-timestamp scheme as Django's password reset token, but
    keyed on is_email_verified so a token is invalidated once used."""

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_email_verified}"


email_verification_token_generator = EmailVerificationTokenGenerator()
