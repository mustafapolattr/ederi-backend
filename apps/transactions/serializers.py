from django.db.models import Q
from rest_framework import serializers

from apps.accounts.models import Account
from apps.categories.models import Category

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.none())
    to_account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.none(), required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none(), required=False, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "to_account",
            "category",
            "type",
            "amount",
            "currency",
            "merchant",
            "description",
            "notes",
            "transaction_date",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "source", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None:
            user = request.user
            # Scope every related-object choice to the requesting user so an
            # attacker can't wire a transaction to someone else's account or
            # category by guessing an id (IDOR, spec §42).
            self.fields["account"].queryset = Account.objects.filter(user=user, is_active=True)
            self.fields["to_account"].queryset = Account.objects.filter(user=user, is_active=True)
            self.fields["category"].queryset = Category.objects.filter(Q(user=user) | Q(user__isnull=True))

    def validate(self, attrs):
        get = lambda field: attrs.get(field, getattr(self.instance, field, None))  # noqa: E731
        type_ = get("type")
        account = get("account")
        to_account = get("to_account")
        amount = get("amount")
        currency = get("currency")

        if type_ == Transaction.TransactionType.TRANSFER:
            if to_account is None:
                raise serializers.ValidationError({"to_account": "Required for transfer transactions."})
            if to_account == account:
                raise serializers.ValidationError({"to_account": "Must be different from the source account."})
            if to_account.currency != account.currency:
                raise serializers.ValidationError(
                    {"to_account": "Must share the source account's currency (no currency conversion in MVP)."}
                )
        elif to_account is not None:
            raise serializers.ValidationError({"to_account": "Only allowed for transfer transactions."})

        if account is not None and currency != account.currency:
            raise serializers.ValidationError(
                {"currency": "Must match the account currency (no currency conversion in MVP)."}
            )

        if type_ == Transaction.TransactionType.ADJUSTMENT:
            if amount is not None and amount == 0:
                raise serializers.ValidationError({"amount": "Adjustment amount must not be zero."})
        elif amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "Must be greater than zero."})

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
