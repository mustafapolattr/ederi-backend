from rest_framework import permissions, viewsets

from apps.core.permissions import IsOwner

from .models import Budget
from .serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = Budget.objects.filter(user=self.request.user).select_related("category")
        month = self.request.query_params.get("month")
        if month:
            year, _, mo = month.partition("-")
            queryset = queryset.filter(start_date__year=year, start_date__month=mo)
        return queryset
