from django.conf import settings
from django.db import models

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.core.models import BaseModel


class Transaction(BaseModel):
    """Financial transaction (spec §16-17).

    amount is stored positive for income/expense/transfer/refund; the sign
    of its effect on account balances is derived from `type` (see
    apps.transactions.services). adjustment is the one type where amount
    itself carries the sign, since it represents a direct balance
    correction delta rather than a real cash movement.
    """

    class TransactionType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"
        TRANSFER = "transfer", "Transfer"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Source(models.TextChoices):
        """Origin of the transaction (spec §57) — only MANUAL is reachable
        via the API in Phase 2; the rest exist so later phases (CSV import,
        bank sync) don't require a schema change."""

        MANUAL = "manual", "Manual"
        CSV = "csv", "CSV import"
        BANK = "bank", "Bank"
        API = "api", "API"
        IMPORT = "import", "Import"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="transactions", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, related_name="transactions", on_delete=models.PROTECT)
    to_account = models.ForeignKey(
        Account,
        related_name="incoming_transfers",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        related_name="transactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    merchant = models.CharField(max_length=150, blank=True)
    description = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    transaction_date = models.DateField()

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["account", "transaction_date"]),
        ]

    def __str__(self):
        return f"{self.type} {self.amount} {self.currency}"
