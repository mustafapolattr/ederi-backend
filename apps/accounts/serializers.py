from rest_framework import serializers

from apps.transactions.services import get_account_balance

from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    """Used for list/retrieve/update. currency and initial_balance are
    immutable once the account exists — changing either would retroactively
    change the meaning of every transaction already booked against this
    account, so PATCH silently ignores them (same pattern as
    ProfileSerializer's immutable email)."""

    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "type",
            "currency",
            "initial_balance",
            "current_balance",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "currency", "initial_balance", "created_at", "updated_at"]

    def get_current_balance(self, obj):
        balance = getattr(obj, "current_balance", None)
        if balance is None:
            balance = get_account_balance(obj)
        # Stringify like every DecimalField on this serializer does
        # (REST_FRAMEWORK's COERCE_DECIMAL_TO_STRING) — money is never a
        # JSON float on the wire (spec §35).
        return str(balance)


class AccountCreateSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
