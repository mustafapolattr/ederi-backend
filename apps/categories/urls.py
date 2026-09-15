from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", CategoryViewSet, basename="category")

urlpatterns = router.urls
