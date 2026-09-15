from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "is_default"]
    list_filter = ["type", "is_default"]
    search_fields = ["name", "user__email"]
