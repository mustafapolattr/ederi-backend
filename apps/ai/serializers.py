from decimal import Decimal

from rest_framework import serializers

from apps.transactions.models import Transaction


class ParseTransactionRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500, allow_blank=False, trim_whitespace=True)


class ParsedTransactionSchemaSerializer(serializers.Serializer):
    """Schema validation for the raw JSON the LLM returns — the first half
    of the required pipeline (spec §20): Structured JSON -> Schema
    Validation -> Business Validation. Business validation happens
    separately, against the real TransactionSerializer, once account_id and
    category_id are resolved to rows the user actually owns."""

    type = serializers.ChoiceField(choices=Transaction.TransactionType.choices)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField(max_length=3, allow_blank=True, required=False, default="")
    account_id = serializers.UUIDField(allow_null=True, required=False, default=None)
    category_id = serializers.UUIDField(allow_null=True, required=False, default=None)
    merchant = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    description = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")
    transaction_date = serializers.DateField()
    clarification = serializers.CharField(allow_blank=True, required=False, default="")


class AnalyzeRequestSerializer(serializers.Serializer):
    """No input today — analysis is always the current month. Kept as an
    explicit (empty) serializer so the view still validates the request
    body shape, and so future params have an obvious home."""


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, allow_blank=False, trim_whitespace=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)


class ScenarioRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.CharField(max_length=3)
    description = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")
