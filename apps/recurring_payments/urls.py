from rest_framework.routers import SimpleRouter

from .views import RecurringPaymentViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", RecurringPaymentViewSet, basename="recurring-payment")

urlpatterns = router.urls
