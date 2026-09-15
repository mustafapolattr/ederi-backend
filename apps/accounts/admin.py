from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "currency", "initial_balance", "is_active"]
    list_filter = ["type", "currency", "is_active"]
    search_fields = ["name", "user__email"]
