from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_dashboard_data


class HealthCheckView(APIView):
    """Unauthenticated liveness probe for Docker/orchestration health checks."""

    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        return Response({"success": True, "status": "ok"})


class DashboardView(APIView):
    """Single aggregated read for the Home screen (spec §14)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"success": True, "data": get_dashboard_data(request.user)})
