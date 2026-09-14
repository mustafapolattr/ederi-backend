from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import DjangoUnicodeDecodeError, force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_email_verified", "created_at"]
        read_only_fields = ["id", "email", "is_email_verified", "created_at"]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UidTokenMixin:
    def decode_uid(self, uid):
        try:
            return force_str(urlsafe_base64_decode(uid))
        except (TypeError, ValueError, OverflowError, DjangoUnicodeDecodeError) as exc:
            raise serializers.ValidationError({"uid": "Invalid uid."}) from exc


class PasswordResetConfirmSerializer(UidTokenMixin, serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class EmailVerificationConfirmSerializer(UidTokenMixin, serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
