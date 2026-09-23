from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "goal_type", "target_amount", "current_amount", "target_date"]
    list_filter = ["goal_type", "currency"]
    search_fields = ["name", "user__email"]
