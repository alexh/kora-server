from functools import wraps

def allow_demo_key(view_func):
    """
    Decorator to mark a view as accessible with demo API keys.
    Must be placed before the api_view or other DRF decorators.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Mark the request as a demo route
        request._demo_route = True
        return view_func(request, *args, **kwargs)
    return wrapped_view 