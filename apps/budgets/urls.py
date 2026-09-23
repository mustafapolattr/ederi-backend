from rest_framework.routers import SimpleRouter

from .views import BudgetViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", BudgetViewSet, basename="budget")

urlpatterns = router.urls
