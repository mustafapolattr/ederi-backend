from rest_framework import permissions, viewsets

from apps.core.permissions import IsOwner
from apps.transactions.services import annotate_balances

from .models import Account
from .serializers import AccountCreateSerializer, AccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = annotate_balances(Account.objects.filter(user=self.request.user))
        if self.action == "list" and self.request.query_params.get("include_inactive") != "true":
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return AccountCreateSerializer
        return AccountSerializer

    def perform_destroy(self, instance):
        # Soft delete (spec §15's is_active exists for exactly this):
        # transactions keep referencing the account, so balance history
        # and net worth stay correct.
        instance.is_active = False
        instance.save(update_fields=["is_active"])
