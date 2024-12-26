from rest_framework.decorators import api_view
from rest_framework.response import Response

try:
    from config.version import VERSION
except ImportError:
    VERSION = 'development'

@api_view(['GET'])
def welcome(request):
    """Welcome endpoint that returns API info"""
    return Response({
        'message': 'Welcome to the UMI API',
        'version': VERSION,
        'status': 'ok'
    }) 