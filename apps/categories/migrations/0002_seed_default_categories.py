import uuid

from django.db import migrations

# Default categories (spec §18). All expense-typed — the spec does not
# define default income categories, and users can create their own custom
# income categories via the existing custom-category feature.
DEFAULT_CATEGORIES = [
    ("Food", "restaurant", "#F97316"),
    ("Transport", "directions_car", "#3B82F6"),
    ("Housing", "home", "#8B5CF6"),
    ("Bills", "receipt_long", "#EF4444"),
    ("Shopping", "shopping_bag", "#EC4899"),
    ("Entertainment", "movie", "#F59E0B"),
    ("Health", "local_hospital", "#10B981"),
    ("Education", "school", "#0EA5E9"),
    ("Travel", "flight", "#14B8A6"),
    ("Subscriptions", "subscriptions", "#6366F1"),
    ("Personal", "person", "#84CC16"),
    ("Other", "category", "#6B7280"),
]


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    for name, icon, color in DEFAULT_CATEGORIES:
        if Category.objects.filter(user__isnull=True, name=name).exists():
            continue
        Category.objects.create(
            id=uuid.uuid4(),
            user=None,
            name=name,
            icon=icon,
            color=color,
            type="expense",
            is_default=True,
        )


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Category.objects.filter(user__isnull=True, is_default=True, name__in=[n for n, _, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
