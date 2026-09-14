from django.urls import include, path

# Versioned API root (spec §39). Feature modules are wired in here as they
# are implemented — most apps are still empty scaffolding (spec §67).
urlpatterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.users.urls")),
]
