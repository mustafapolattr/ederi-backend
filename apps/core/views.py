from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Unauthenticated liveness probe for Docker/orchestration health checks."""

    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        return Response({"success": True, "status": "ok"})
