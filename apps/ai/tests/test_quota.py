import pytest
from rest_framework.exceptions import Throttled

from apps.ai import quota
from apps.ai.models import AIUsageLog
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestQuota:
    def test_allows_requests_under_the_limit(self, settings):
        settings.AI_DAILY_REQUEST_LIMIT = 3
        user = UserFactory()
        AIUsageLog.objects.create(user=user, endpoint="chat")

        quota.assert_within_daily_limit(user)  # should not raise

    def test_blocks_requests_at_the_limit(self, settings):
        settings.AI_DAILY_REQUEST_LIMIT = 2
        user = UserFactory()
        AIUsageLog.objects.create(user=user, endpoint="chat")
        AIUsageLog.objects.create(user=user, endpoint="chat")

        with pytest.raises(Throttled):
            quota.assert_within_daily_limit(user)

    def test_limit_is_per_user(self, settings):
        settings.AI_DAILY_REQUEST_LIMIT = 1
        user = UserFactory()
        other = UserFactory()
        AIUsageLog.objects.create(user=other, endpoint="chat")

        quota.assert_within_daily_limit(user)  # other user's usage doesn't count

    def test_record_usage_creates_a_row(self):
        user = UserFactory()

        quota.record_usage(user, "analyze")

        assert AIUsageLog.objects.filter(user=user, endpoint="analyze").count() == 1
