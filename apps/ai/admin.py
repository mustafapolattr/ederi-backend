from django.contrib import admin

from .models import AIConversation, AIMessage, AIUsageLog


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ["role", "content", "created_at"]
    can_delete = False


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "created_at"]
    search_fields = ["user__email"]
    inlines = [AIMessageInline]


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ["user", "endpoint", "created_at"]
    list_filter = ["endpoint"]
    search_fields = ["user__email"]
