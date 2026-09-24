from django.contrib import admin

from .models import RecurringPayment


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "amount", "currency", "frequency", "next_payment_date", "is_active"]
    list_filter = ["type", "frequency", "currency", "is_active"]
    search_fields = ["name", "user__email"]
