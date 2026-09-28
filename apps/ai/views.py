from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import quota, services
from .serializers import (
    AnalyzeRequestSerializer,
    ChatRequestSerializer,
    ParseTransactionRequestSerializer,
    ScenarioRequestSerializer,
)


class ParseTransactionView(APIView):
    """AI transaction entry (spec §20). Never writes to the database — the
    client confirms via the normal POST /transactions endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ParseTransactionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quota.assert_within_daily_limit(request.user)
        data = services.parse_transaction_text(request, serializer.validated_data["text"])
        quota.record_usage(request.user, "parse-transaction")

        return Response({"success": True, "data": data})


class AnalyzeView(APIView):
    """AI spending analysis (spec §27)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        AnalyzeRequestSerializer(data=request.data).is_valid(raise_exception=True)

        quota.assert_within_daily_limit(request.user)
        data = services.analyze_spending(request.user)
        quota.record_usage(request.user, "analyze")

        return Response({"success": True, "data": data})


class ChatView(APIView):
    """AI financial assistant chat (spec §28-29)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quota.assert_within_daily_limit(request.user)
        data = services.send_chat_message(
            request,
            message=serializer.validated_data["message"],
            conversation_id=serializer.validated_data.get("conversation_id"),
        )
        quota.record_usage(request.user, "chat")

        return Response({"success": True, "data": data})


class ScenarioView(APIView):
    """AI what-if scenario (spec §31)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScenarioRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quota.assert_within_daily_limit(request.user)
        data = services.run_scenario(
            request.user,
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data["currency"],
            description=serializer.validated_data.get("description", ""),
        )
        quota.record_usage(request.user, "scenario")

        return Response({"success": True, "data": data})
