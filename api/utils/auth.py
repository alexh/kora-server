from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from functools import wraps
from django.http import JsonResponse

def admin_required(view_func):
    """
    Decorator to check for admin API key.
    Works with both function-based views and viewset methods.
    """
    @wraps(view_func)
    def wrapped_view(self_or_request, request_or_first_arg, *args, **kwargs):
        # Handle both viewset methods and function-based views
        if hasattr(self_or_request, 'request'):
            # This is a viewset method
            request = self_or_request.request
        elif hasattr(request_or_first_arg, 'META'):
            # This is a function-based view
            request = request_or_first_arg
            self_or_request = None
        else:
            request = getattr(request_or_first_arg, '_request', request_or_first_arg)
            
        # Check multiple possible header variations
        admin_key = (
            request.headers.get('X-Admin-Key') or
            request.headers.get('x-admin-key') or
            request.META.get('HTTP_X_ADMIN_KEY')
        )
        
        if not admin_key or admin_key != settings.ADMIN_API_KEY:
            return JsonResponse(
                {'error': 'Unauthorized - Invalid or missing X-Admin-Key header'}, 
                status=401
            )

        if self_or_request is None:
            # Function-based view
            return view_func(request_or_first_arg, *args, **kwargs)
        else:
            # Viewset method
            return view_func(self_or_request, request_or_first_arg, *args, **kwargs)
            
    return wrapped_view

def allow_demo_key(view_func):
    """
    Decorator to mark a view as accessible with demo API keys.
    Works with both function-based views and viewset methods.
    Must be placed before the api_view or other DRF decorators.
    """
    @wraps(view_func)
    def wrapped_view(self_or_request, request_or_first_arg, *args, **kwargs):
        # Handle both viewset methods and function-based views
        if hasattr(self_or_request, 'request'):
            # This is a viewset method - DRF ViewSet
            request = self_or_request.request
            # Set the flag on both the viewset request and the underlying request
            request._demo_route = True
            self_or_request.request._demo_route = True
        elif hasattr(request_or_first_arg, 'META'):
            # This is a function-based view
            request = request_or_first_arg
            request._demo_route = True
        else:
            # Handle other cases
            request = getattr(request_or_first_arg, '_request', request_or_first_arg)
            request._demo_route = True
            # Also set it on the parent request if it exists
            if hasattr(request_or_first_arg, 'request'):
                request_or_first_arg.request._demo_route = True

        # Call the view function with original arguments
        if hasattr(self_or_request, 'request'):
            return view_func(self_or_request, request_or_first_arg, *args, **kwargs)
        else:
            return view_func(request, *args, **kwargs)
    return wrapped_view 