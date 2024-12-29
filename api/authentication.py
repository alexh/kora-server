from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Check multiple possible header variations
        api_key = (
            request.META.get('HTTP_X_API_KEY') or
            request.META.get('HTTP_X_Api_Key') or
            request.META.get('HTTP_X_API_KEY') or
            request.META.get('HTTP_X_Api_key') or
            request.headers.get('X-API-Key') or
            request.headers.get('x-api-key')
        )
        
        logger.info(f"Received API key: {api_key}")
        logger.info(f"Expected API key: {settings.API_KEY}")
        logger.info(f"Demo API keys: {settings.DEMO_API_KEYS}")
        
        if not api_key:
            logger.warning("No API key provided in request")
            raise AuthenticationFailed('No API key provided')
        
        expected_api_key = settings.API_KEY
        if not expected_api_key:
            logger.error("No API key configured on server")
            raise AuthenticationFailed('API key not configured on server')
            
        # Check if this is a demo route and if the key is in the demo keys list
        is_demo_route = (
            getattr(request, '_demo_route', False) or
            getattr(getattr(request, '_request', None), '_demo_route', False)
        )
        
        logger.info(f"Demo route check:")
        logger.info(f"  - is_demo_route: {is_demo_route}")
        logger.info(f"  - api_key in demo_keys: {api_key in settings.DEMO_API_KEYS}")
        logger.info(f"  - demo_keys list: {settings.DEMO_API_KEYS}")
        
        if is_demo_route and api_key in settings.DEMO_API_KEYS:
            logger.info("Demo API key authentication successful")
            return (None, api_key)
            
        if api_key != expected_api_key:
            logger.warning(f"Invalid API key provided: {api_key}")
            raise AuthenticationFailed('Invalid API key')
            
        logger.info("Standard API key authentication successful")
        return (None, api_key)

    def authenticate_header(self, request):
        return 'X-Api-Key'  # Match the case you're using in the client 