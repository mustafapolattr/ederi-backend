from rest_framework import serializers

from .models import Goal
from .services import get_remaining_amount, get_required_monthly_contribution


class GoalSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.SerializerMethodField()
    required_monthly_contribution = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "id",
            "name",
            "goal_type",
            "target_amount",
            "current_amount",
            "currency",
            "target_date",
            "remaining_amount",
            "required_monthly_contribution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_remaining_amount(self, obj):
        return str(get_remaining_amount(obj))

    def get_required_monthly_contribution(self, obj):
        return str(get_required_monthly_contribution(obj))

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Must be greater than zero.")
        return value

    def validate_current_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Must not be negative.")
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
