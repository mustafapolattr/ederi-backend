from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Goal(BaseModel):
    """Savings goal (spec §23)."""

    class GoalType(models.TextChoices):
        EMERGENCY_FUND = "emergency_fund", "Emergency fund"
        VACATION = "vacation", "Vacation"
        CAR = "car", "Car"
        HOME = "home", "Home"
        EDUCATION = "education", "Education"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="goals", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    goal_type = models.CharField(max_length=20, choices=GoalType.choices, default=GoalType.CUSTOM)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3)
    target_date = models.DateField()

    class Meta:
        ordering = ["target_date"]
        indexes = [
            models.Index(fields=["user", "target_date"]),
        ]

    def __str__(self):
        return self.name
