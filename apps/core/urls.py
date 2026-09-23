from django.urls import path

from .views import DashboardView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
