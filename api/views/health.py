from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([])  # No authentication
@permission_classes([AllowAny])  # Allow all access
def health_check(request):
    """Super simple health check that just returns 200 OK"""
    logger.info("Health check endpoint called")
    try:
        return Response({'status': 'ok'}, status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({'status': 'error'}, status=500) 