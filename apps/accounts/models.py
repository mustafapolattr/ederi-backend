from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Account(BaseModel):
    """Financial account (spec §15).

    current_balance is intentionally NOT stored here — it is derived from
    initial_balance plus the ledger of transactions that reference this
    account (see apps.accounts.services.get_account_balance). A single
    source of truth avoids balance drift between the stored value and the
    transaction history, which matters more for correctness than the cost
    of an aggregate query (spec §19, §53).
    """

    class AccountType(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank"
        CREDIT_CARD = "credit_card", "Credit card"
        SAVINGS = "savings", "Savings"
        INVESTMENT = "investment", "Investment"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AccountType.choices)
    currency = models.CharField(max_length=3)
    initial_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.currency})"
