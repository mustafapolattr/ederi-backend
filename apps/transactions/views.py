from rest_framework import permissions, viewsets

from apps.core.permissions import IsOwner

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related(
            "account", "to_account", "category"
        )
        params = self.request.query_params

        account_id = params.get("account")
        if account_id:
            queryset = queryset.filter(account_id=account_id)

        category_id = params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        type_ = params.get("type")
        if type_:
            queryset = queryset.filter(type=type_)

        date_from = params.get("date_from")
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)

        date_to = params.get("date_to")
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)

        return queryset
