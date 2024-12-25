"""URL Configuration for the API app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from api.views import (
    IssueViewSet,
    ProductIdeaViewSet,
    StoreViewSet
)
from api.views.health import health_check
from version import VERSION

# Root view
def welcome(request):
    return JsonResponse({
        "message": f"welcome to UMI-OS v{VERSION}"
    })

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'issues', IssueViewSet)
router.register(r'product-ideas', ProductIdeaViewSet)
router.register(r'store', StoreViewSet, basename='store')

# The health check should be before the router URLs
urlpatterns = [
    path('', welcome, name='welcome'),
    path('api/health/', health_check, name='health-check'),
    path('api/', include(router.urls)),
] 