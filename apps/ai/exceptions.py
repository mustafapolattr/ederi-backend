from rest_framework.exceptions import APIException


class AIServiceUnavailable(APIException):
    """The LLM provider could not be reached, or returned something we
    couldn't use (network failure, non-200, unparseable content)."""

    status_code = 502
    default_detail = "AI service is temporarily unavailable. Please try again later."
    default_code = "ai_service_error"


class AIRateLimited(APIException):
    """The LLM provider itself rate-limited this request (its HTTP 429),
    distinct from our own daily-quota throttle in apps.ai.quota."""

    status_code = 503
    default_detail = "AI is busy right now. Please try again shortly."
    default_code = "ai_rate_limited"
