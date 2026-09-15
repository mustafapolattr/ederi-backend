from rest_framework.routers import SimpleRouter

from .views import TransactionViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", TransactionViewSet, basename="transaction")

urlpatterns = router.urls
