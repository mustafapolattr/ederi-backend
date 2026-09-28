"""LLM provider isolation.

This is the ONLY module in the codebase that knows the provider is Gemini —
swapping providers later means editing only this file. Model name and API
key come from env (LLM_MODEL, LLM_API_KEY) so they can change without a code
change too.

The LLM is never the source of truth for financial numbers (spec §30-31):
every caller of generate() must only ask it to explain/format numbers the
backend already computed, never to compute them itself.
"""

import requests
from django.conf import settings

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_TIMEOUT_SECONDS = 20


class LLMError(Exception):
    """Base error for any LLM provider failure (network, non-200, or an
    unparseable response body)."""


class LLMRateLimitedError(LLMError):
    """The provider rejected the request because of its own rate limiting
    (HTTP 429), as opposed to any other failure."""


def generate(prompt: str, *, max_output_tokens: int = 256) -> str:
    """Send `prompt` to the configured LLM and return its raw text output."""

    if not settings.LLM_API_KEY:
        raise LLMError("LLM_API_KEY is not configured.")

    url = _ENDPOINT.format(model=settings.LLM_MODEL)
    try:
        response = requests.post(
            url,
            params={"key": settings.LLM_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_output_tokens,
                    "temperature": 0,
                },
            },
            timeout=_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise LLMError(f"Request to LLM provider failed: {exc}") from exc

    if response.status_code == 429:
        raise LLMRateLimitedError("LLM provider rate limit exceeded.")
    if response.status_code != 200:
        raise LLMError(f"LLM provider returned HTTP {response.status_code}.")

    try:
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LLMError(f"Unexpected LLM response shape: {exc}") from exc
