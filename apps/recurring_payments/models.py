from django.conf import settings
from django.db import models

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.core.models import BaseModel


class RecurringPayment(BaseModel):
    """Recurring income or expense (spec §24)."""

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    class Type(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="recurring_payments", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    next_payment_date = models.DateField()
    category = models.ForeignKey(
        Category,
        related_name="recurring_payments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    account = models.ForeignKey(Account, related_name="recurring_payments", on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["next_payment_date"]
        indexes = [
            models.Index(fields=["user", "is_active", "next_payment_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.frequency})"
