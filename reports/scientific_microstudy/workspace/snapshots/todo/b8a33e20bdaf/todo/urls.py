from rest_framework.routers import DefaultRouter

from todo.views import ProjectViewSet, TagViewSet, TaskViewSet

router = DefaultRouter()
router.register(r"tasks", TaskViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"tags", TagViewSet)

urlpatterns = router.urls
