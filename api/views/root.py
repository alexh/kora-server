from rest_framework.decorators import api_view
from rest_framework.response import Response

try:
    from config.version import VERSION
except ImportError:
    VERSION = 'development'

@api_view(['GET'])
def root(request):
    """Root endpoint that returns API version"""
    return Response({
        'version': VERSION,
        'status': 'ok'
    }) 