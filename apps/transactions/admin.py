from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "account", "type", "amount", "currency", "transaction_date"]
    list_filter = ["type", "source", "currency"]
    search_fields = ["merchant", "description", "user__email"]
