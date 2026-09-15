from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Category(BaseModel):
    """Transaction category (spec §18).

    user=None means a global default category, shared read-only across all
    users and seeded by a data migration. A category with user set is a
    custom category owned (and exclusively editable/deletable) by that user.
    """

    class CategoryType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"
        BOTH = "both", "Both"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="categories",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)
    type = models.CharField(max_length=10, choices=CategoryType.choices)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        return self.name
