from django.contrib.auth.tokens import default_token_generator
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .models import User
from .serializers import (
    EmailVerificationConfirmSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
)
from .tokens import email_verification_token_generator


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def perform_create(self, serializer):
        user = serializer.save()
        services.send_verification_email(user)
        return user


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise ValidationError({"refresh": "This field is required."})
        try:
            RefreshToken(refresh).blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": "Invalid or expired token."}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"].lower()).first()
        if user is not None:
            services.send_password_reset_email(user)
        # Always return the same response so this endpoint doesn't leak
        # which emails are registered.
        return Response({"success": True, "message": "If that email exists, a reset link was sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.decode_uid(serializer.validated_data["uid"])
        user = User.objects.filter(pk=uid).first()
        token = serializer.validated_data["token"]
        if user is None or not default_token_generator.check_token(user, token):
            raise ValidationError({"token": "Invalid or expired token."})
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"success": True, "message": "Password updated."})


class EmailVerificationConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.decode_uid(serializer.validated_data["uid"])
        user = User.objects.filter(pk=uid).first()
        token = serializer.validated_data["token"]
        if user is None or not email_verification_token_generator.check_token(user, token):
            raise ValidationError({"token": "Invalid or expired token."})
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return Response({"success": True, "message": "Email verified."})


class EmailVerificationResendView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        if request.user.is_email_verified:
            return Response({"success": True, "message": "Email already verified."})
        services.send_verification_email(request.user)
        return Response({"success": True, "message": "Verification email sent."})
