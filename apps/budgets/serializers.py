from django.db.models import Q
from rest_framework import serializers

from apps.categories.models import Category

from .models import Budget
from .services import get_budget_remaining, get_budget_spent


class BudgetSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none())
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "amount",
            "currency",
            "period",
            "start_date",
            "end_date",
            "spent",
            "remaining",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "period", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None:
            # Scope category choices to the requesting user (IDOR, spec §42),
            # same pattern as TransactionSerializer.
            self.fields["category"].queryset = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True))

    def get_spent(self, obj):
        return str(get_budget_spent(obj))

    def get_remaining(self, obj):
        return str(get_budget_remaining(obj))

    def validate(self, attrs):
        get = lambda field: attrs.get(field, getattr(self.instance, field, None))  # noqa: E731
        category = get("category")
        start_date = get("start_date")
        end_date = get("end_date")
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "Must not be before start_date."})

        request = self.context.get("request")
        if request is not None and category and start_date and end_date:
            # user isn't a serializer field, so the model's unique constraint
            # can't be enforced automatically — check it here instead.
            duplicates = Budget.objects.filter(
                user=request.user, category=category, start_date=start_date, end_date=end_date
            )
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError({"category": "A budget already exists for this category and period."})

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
