from rest_framework import routers
from .views import HealthCheckViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r'health', HealthCheckViewSet, basename='health')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls
