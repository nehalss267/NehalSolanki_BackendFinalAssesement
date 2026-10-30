from django.urls import path
from rest_framework import routers

from .views import (
    HealthCheckViewSet,
    JobListView,
    JobStatisticsView,
    ScanCancelView,
    ScanRemoveView,
    ScanResultView,
    ScanStartView,
    ScanStatusView,
    UserViewSet,
    V1HealthView,
)

router = routers.DefaultRouter()
router.register(r'health', HealthCheckViewSet, basename='health')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('v1/health', V1HealthView.as_view(), name='v1-health'),
    path('v1/scan/start', ScanStartView.as_view(), name='v1-scan-start'),
    path('v1/scan/status/<uuid:job_id>', ScanStatusView.as_view(), name='v1-scan-status'),
    path('v1/scan/result/<uuid:job_id>', ScanResultView.as_view(), name='v1-scan-result'),
    path('v1/scan/cancel/<uuid:job_id>', ScanCancelView.as_view(), name='v1-scan-cancel'),
    path('v1/scan/remove/<uuid:job_id>', ScanRemoveView.as_view(), name='v1-scan-remove'),
    path('v1/jobs/jobs', JobListView.as_view(), name='v1-jobs-list'),
    path('v1/jobs/statistics', JobStatisticsView.as_view(), name='v1-jobs-statistics'),
] + router.urls
