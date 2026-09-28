"""AIConversation/AIMessage/AIUsageLog — Phase 5 (spec §20, §28-31, §60)."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class AIConversation(BaseModel):
    """A chat thread between a user and the AI assistant (spec §28-29)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="ai_conversations", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"Conversation {self.id} ({self.user_id})"


class AIMessage(BaseModel):
    """One turn of an AIConversation."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    conversation = models.ForeignKey(AIConversation, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class AIUsageLog(BaseModel):
    """One row per successful AI request, counted per user per day to
    enforce the daily quota (see apps.ai.quota)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="ai_usage_logs", on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=30)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user_id} {self.endpoint} {self.created_at}"
