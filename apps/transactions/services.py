"""Deterministic account-balance math (spec §17, §25, §51).

Account.current_balance is never stored — it is always derived from
initial_balance plus the ledger of transactions, so there is exactly one
source of truth and no denormalized value that can drift out of sync.
"""

from decimal import Decimal

from django.db.models import Case, DecimalField, F, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce

from .models import Transaction

MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)

_SOURCE_EFFECT = Case(
    When(
        type__in=[
            Transaction.TransactionType.INCOME,
            Transaction.TransactionType.REFUND,
            Transaction.TransactionType.ADJUSTMENT,
        ],
        then=F("amount"),
    ),
    When(
        type__in=[Transaction.TransactionType.EXPENSE, Transaction.TransactionType.TRANSFER],
        then=-F("amount"),
    ),
    default=Value(0),
    output_field=MONEY_FIELD,
)


def get_account_balance(account) -> Decimal:
    """Compute a single account's current balance with two aggregate queries.

    Two separate queries (rather than one query joining both the `account`
    and `to_account` reverse relations) avoid a join-explosion that would
    silently multiply and corrupt the sums.
    """

    source_total = Transaction.objects.filter(account=account).aggregate(
        total=Coalesce(Sum(_SOURCE_EFFECT), Value(0), output_field=MONEY_FIELD)
    )["total"]

    incoming_transfer_total = Transaction.objects.filter(
        to_account=account, type=Transaction.TransactionType.TRANSFER
    ).aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=MONEY_FIELD))["total"]

    # account.initial_balance may still be a plain str/int here if the
    # instance was just constructed in memory (Django does not coerce a
    # DecimalField's value on assignment, only on save) — Decimal() is a
    # no-op for an already-Decimal value.
    initial_balance = Decimal(str(account.initial_balance))
    return initial_balance + source_total + incoming_transfer_total


def annotate_balances(accounts_queryset):
    """Attach `current_balance` to every row of an Account queryset in two
    extra queries total, instead of one query per account (spec §53)."""

    source_effect_sq = (
        Transaction.objects.filter(account=OuterRef("pk"))
        .values("account")
        .annotate(total=Sum(_SOURCE_EFFECT))
        .values("total")
    )
    incoming_transfer_sq = (
        Transaction.objects.filter(to_account=OuterRef("pk"), type=Transaction.TransactionType.TRANSFER)
        .values("to_account")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    return accounts_queryset.annotate(
        _source_effect=Coalesce(Subquery(source_effect_sq, output_field=MONEY_FIELD), Value(0), output_field=MONEY_FIELD),
        _incoming_transfer_effect=Coalesce(
            Subquery(incoming_transfer_sq, output_field=MONEY_FIELD), Value(0), output_field=MONEY_FIELD
        ),
    ).annotate(
        current_balance=F("initial_balance") + F("_source_effect") + F("_incoming_transfer_effect"),
    )
