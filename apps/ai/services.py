"""AI endpoint orchestration (spec §20-21, §27-31).

Every function here follows the same shape: gather already-computed backend
facts (never raw transaction lists, spec §29/§45) -> build a prompt ->
call the LLM -> turn LLM failures into apps.ai.exceptions -> hand back a
result where every number came from the backend, never from the LLM.
"""

import datetime
import json
import re
from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.core.services import (
    get_available_to_spend_by_currency,
    get_budget_statuses,
    get_dashboard_data,
    get_this_month_by_currency,
)
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer

from . import llm, prompts
from .exceptions import AIRateLimited, AIServiceUnavailable
from .models import AIConversation, AIMessage
from .serializers import ParsedTransactionSchemaSerializer

MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _call_llm(prompt: str, *, max_output_tokens: int) -> str:
    """Shared LLM call + error translation for every AI endpoint."""
    try:
        return llm.generate(prompt, max_output_tokens=max_output_tokens)
    except llm.LLMRateLimitedError as exc:
        raise AIRateLimited() from exc
    except llm.LLMError as exc:
        raise AIServiceUnavailable() from exc


def _extract_json(raw: str) -> dict:
    cleaned = _FENCE_RE.sub("", raw).strip()
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AIServiceUnavailable(
            "AI returned an unexpected response. Please try again or enter the transaction manually."
        ) from exc
    if not isinstance(parsed, dict):
        raise AIServiceUnavailable(
            "AI returned an unexpected response. Please try again or enter the transaction manually."
        )
    return parsed


# ---------------------------------------------------------------------------
# parse-transaction (spec §20-21)
# ---------------------------------------------------------------------------


def _proposed_fields(data: dict, *, account_id) -> dict:
    return {
        "type": data.get("type"),
        "amount": str(data["amount"]) if data.get("amount") is not None else None,
        "currency": data.get("currency") or None,
        "account": str(account_id) if account_id else None,
        "category": None,
        "merchant": data.get("merchant", ""),
        "description": data.get("description", ""),
        "transaction_date": data["transaction_date"].isoformat() if data.get("transaction_date") else None,
    }


def parse_transaction_text(request, text: str) -> dict:
    user = request.user
    accounts = list(Account.objects.filter(user=user, is_active=True).values("id", "name", "type", "currency"))
    categories = list(
        Category.objects.filter(Q(user=user) | Q(user__isnull=True)).values("id", "name", "type")
    )

    prompt = prompts.build_parse_transaction_prompt(
        text=text, accounts=accounts, categories=categories, today=timezone.localdate()
    )
    raw = _call_llm(prompt, max_output_tokens=300)
    parsed_json = _extract_json(raw)

    schema = ParsedTransactionSchemaSerializer(data=parsed_json)
    if not schema.is_valid():
        raise AIServiceUnavailable(
            "AI returned an unexpected response. Please try again or enter the transaction manually."
        )
    data = schema.validated_data

    account_ids = {a["id"] for a in accounts}
    account_id = data.get("account_id")
    if account_id is None or account_id not in account_ids:
        return {
            "transaction": _proposed_fields(data, account_id=None),
            "valid": False,
            "errors": None,
            "needs_clarification": data.get("clarification") or "Which account did you use?",
        }

    category_ids = {c["id"] for c in categories}
    category_id = data.get("category_id")
    if category_id not in category_ids:
        category_id = None

    account_currency = next(a["currency"] for a in accounts if a["id"] == account_id)
    tx_payload = {
        "type": data["type"],
        "amount": data["amount"],
        "currency": data.get("currency") or account_currency,
        "account": str(account_id),
        "category": str(category_id) if category_id else None,
        "merchant": data.get("merchant", "")[:150],
        "description": data.get("description", "")[:255],
        "transaction_date": data["transaction_date"],
    }

    tx_serializer = TransactionSerializer(data=tx_payload, context={"request": request})
    valid = tx_serializer.is_valid()

    return {
        "transaction": {
            **tx_payload,
            "amount": str(tx_payload["amount"]),
            "transaction_date": tx_payload["transaction_date"].isoformat(),
        },
        "valid": valid,
        "errors": None if valid else tx_serializer.errors,
        "needs_clarification": None,
    }


# ---------------------------------------------------------------------------
# analyze (spec §27)
# ---------------------------------------------------------------------------


def get_category_spending_comparison(user) -> list:
    """This-month vs last-month expense totals per category — deterministic
    backend aggregation; the LLM only ever narrates this, never computes it."""
    today = timezone.localdate()
    this_start = today.replace(day=1)
    last_end = this_start - datetime.timedelta(days=1)
    last_start = last_end.replace(day=1)

    def totals_by_category(start, end):
        rows = (
            Transaction.objects.filter(
                user=user,
                type=Transaction.TransactionType.EXPENSE,
                transaction_date__gte=start,
                transaction_date__lte=end,
            )
            .values("category__name", "currency")
            .annotate(total=Coalesce(Sum("amount"), Value(0), output_field=MONEY_FIELD))
        )
        return {(row["category__name"] or "Uncategorized", row["currency"]): row["total"] for row in rows}

    this_month = totals_by_category(this_start, today)
    last_month = totals_by_category(last_start, last_end)

    result = []
    for category, currency in sorted(set(this_month) | set(last_month)):
        result.append(
            {
                "category": category,
                "currency": currency,
                "this_month": str(this_month.get((category, currency), Decimal("0.00"))),
                "last_month": str(last_month.get((category, currency), Decimal("0.00"))),
            }
        )
    return result


def analyze_spending(user) -> dict:
    facts = {
        "this_month": get_this_month_by_currency(user),
        "category_comparison": get_category_spending_comparison(user),
        "budgets": get_budget_statuses(user),
    }
    prompt = prompts.build_analyze_prompt(facts)
    insight = _call_llm(prompt, max_output_tokens=200)
    return {"insight": insight.strip(), "facts": facts}


# ---------------------------------------------------------------------------
# chat (spec §28-29)
# ---------------------------------------------------------------------------


def send_chat_message(request, message: str, conversation_id=None) -> dict:
    user = request.user
    if conversation_id:
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)
    else:
        conversation = AIConversation.objects.create(user=user)

    history = list(conversation.messages.order_by("-created_at")[:6])[::-1]

    AIMessage.objects.create(conversation=conversation, role=AIMessage.Role.USER, content=message)

    facts = get_dashboard_data(user)
    prompt = prompts.build_chat_prompt(message=message, history=history, facts=facts)
    answer = _call_llm(prompt, max_output_tokens=250).strip()

    AIMessage.objects.create(conversation=conversation, role=AIMessage.Role.ASSISTANT, content=answer)

    return {"conversation_id": str(conversation.id), "message": answer}


# ---------------------------------------------------------------------------
# scenario (spec §31)
# ---------------------------------------------------------------------------


def run_scenario(user, amount: Decimal, currency: str, description: str = "") -> dict:
    available = {
        row["currency"]: Decimal(row["available_to_spend"]) for row in get_available_to_spend_by_currency(user)
    }
    current = available.get(currency, Decimal("0.00"))
    projected = current - amount

    facts = {
        "currency": currency,
        "current_available_to_spend": str(current),
        "hypothetical_amount": str(amount),
        "projected_available_to_spend": str(projected),
        "description": description,
    }
    prompt = prompts.build_scenario_prompt(facts)
    explanation = _call_llm(prompt, max_output_tokens=150).strip()

    facts["explanation"] = explanation
    return facts
