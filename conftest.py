import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_django_cache():
    """DRF throttling stores request counts in the Django cache, which
    otherwise leaks state between tests (e.g. ScopedRateThrottle on auth
    endpoints)."""
    cache.clear()
    yield
