from django.db.models import Q
from rest_framework import serializers

from apps.accounts.models import Account
from apps.categories.models import Category

from .models import RecurringPayment


class RecurringPaymentSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.none())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none(), required=False, allow_null=True)

    class Meta:
        model = RecurringPayment
        fields = [
            "id",
            "name",
            "type",
            "amount",
            "currency",
            "frequency",
            "next_payment_date",
            "category",
            "account",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None:
            # Scope choices to the requesting user (IDOR, spec §42), same
            # pattern as TransactionSerializer/BudgetSerializer.
            self.fields["account"].queryset = Account.objects.filter(user=request.user)
            self.fields["category"].queryset = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True))

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Must be greater than zero.")
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
