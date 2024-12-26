from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from functools import wraps

def admin_required(view_func):
    """Decorator to check for admin API key"""
    @wraps(view_func)
    def _wrapped_view(viewset, request, *args, **kwargs):
        admin_key = request.META.get('HTTP_X_ADMIN_KEY')
        if not admin_key or admin_key != settings.ADMIN_API_KEY:
            return Response({
                'error': 'Invalid or missing admin key'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return view_func(viewset, request, *args, **kwargs)
    return _wrapped_view 