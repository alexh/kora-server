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
from .views import calendar

# Root view can be moved to api/views/root.py if you prefer
def api_root(request):
    return JsonResponse({
        "version": VERSION,
        "message": f"Welcome to UMI-OS v{VERSION}"
    })

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'issues', IssueViewSet)
router.register(r'product-ideas', ProductIdeaViewSet)
router.register(r'store', StoreViewSet, basename='store')
router.register(r'calendar', calendar.CalendarViewSet, basename='calendar')

# The API routes should all be under /api/
urlpatterns = [
    path('api/', api_root, name='api-root'),
    path('api/health/', health_check, name='health-check'),
    path('api/', include(router.urls)),
] 