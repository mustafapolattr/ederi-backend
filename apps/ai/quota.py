"""Per-user daily AI request quota (cost-control rule for Phase 5).

Checked BEFORE calling the LLM (assert_within_daily_limit) and recorded
AFTER a successful LLM call (record_usage) — usage is only counted once the
cost has actually been incurred, regardless of whether the AI's suggestion
later fails business validation.
"""

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import Throttled

from .models import AIUsageLog


def assert_within_daily_limit(user):
    today = timezone.localdate()
    count = AIUsageLog.objects.filter(user=user, created_at__date=today).count()
    if count >= settings.AI_DAILY_REQUEST_LIMIT:
        raise Throttled(detail="Daily AI request limit reached. Please try again tomorrow.")


def record_usage(user, endpoint: str):
    AIUsageLog.objects.create(user=user, endpoint=endpoint)
