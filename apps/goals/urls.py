from rest_framework.routers import SimpleRouter

from .views import GoalViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", GoalViewSet, basename="goal")

urlpatterns = router.urls
