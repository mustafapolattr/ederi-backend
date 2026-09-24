from rest_framework import permissions, viewsets

from apps.core.permissions import IsOwner

from .models import RecurringPayment
from .serializers import RecurringPaymentSerializer


class RecurringPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringPaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return RecurringPayment.objects.filter(user=self.request.user).select_related("category", "account")
