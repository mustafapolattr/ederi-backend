from rest_framework.routers import SimpleRouter

from .views import AccountViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", AccountViewSet, basename="account")

urlpatterns = router.urls
