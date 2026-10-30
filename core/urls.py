"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.renderers import SwaggerJSONRenderer, SwaggerYAMLRenderer
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Backend Project API",
        default_version='v1',
        description=(
            "Interactive API documentation for the Backend Project.\n\n"
            "**Data extraction endpoints**\n"
            "- `POST /api/v1/scan/start` - Start an extraction job\n"
            "- `GET /api/v1/scan/status/{job_id}` - Get job status\n"
            "- `GET /api/v1/scan/result/{job_id}` - Get extracted records\n"
            "- `POST /api/v1/scan/cancel/{job_id}` - Cancel a job\n"
            "- `DELETE /api/v1/scan/remove/{job_id}` - Remove a job and its data\n"
            "- `GET /api/v1/jobs/jobs` - List extraction jobs\n"
            "- `GET /api/v1/jobs/statistics` - Get aggregate statistics\n"
            "- `GET /api/v1/health` - Service health check\n\n"
            "**Example endpoints**\n"
            "- `GET /api/health/` - Service health check\n"
            "- `GET /api/health/ping/` - Ping the service\n"
            "- `GET /api/users/` - List users\n"
            "- `GET /api/users/{id}/` - Retrieve a user\n"
        ),
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-docs'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path(
        'swagger.json',
        schema_view.as_cached_view(cache_timeout=0, renderer_classes=[SwaggerJSONRenderer]),
        name='schema-json',
    ),
    path(
        'swagger.yaml',
        schema_view.as_cached_view(cache_timeout=0, renderer_classes=[SwaggerYAMLRenderer]),
        name='schema-yaml',
    ),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-root'),
]
