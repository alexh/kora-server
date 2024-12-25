from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from config.version import VERSION

@api_view(['GET'])
@authentication_classes([])  # No authentication required
@permission_classes([])      # No permissions required
def welcome(request):
    return Response({
        "message": f"welcome to UMI-OS v{VERSION}"
    }) 