from django.conf import settings
from django.db import models

from apps.categories.models import Category
from apps.core.models import BaseModel


class Budget(BaseModel):
    """Per-category spending limit for a period (spec §22).

    Only "monthly" periods are supported in Phase 3 — `period` exists for
    spec-field parity and to avoid a schema change if weekly/yearly budgets
    are added later.
    """

    class Period(models.TextChoices):
        MONTHLY = "monthly", "Monthly"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="budgets", on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name="budgets", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    period = models.CharField(max_length=10, choices=Period.choices, default=Period.MONTHLY)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "start_date", "end_date"],
                name="unique_budget_per_category_period",
            )
        ]
        indexes = [
            models.Index(fields=["user", "start_date", "end_date"]),
        ]

    def __str__(self):
        return f"{self.category.name} {self.start_date:%Y-%m}"
