class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow HTTP for health checks
        if request.path == '/api/health/':
            request.is_secure = lambda: True
        return self.get_response(request) 