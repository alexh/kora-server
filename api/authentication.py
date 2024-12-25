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
        
        
        if not api_key:
            logger.warning("No API key provided in request")
            raise AuthenticationFailed('No API key provided')
        
        expected_api_key = settings.API_KEY
        if not expected_api_key:
            logger.error("No API key configured on server")
            raise AuthenticationFailed('API key not configured on server')
            
        if api_key != expected_api_key:
            logger.warning("Invalid API key provided")
            raise AuthenticationFailed('Invalid API key')
            
        logger.debug("API key authentication successful")
        return (None, api_key)  # Return the API key as the auth token

    def authenticate_header(self, request):
        return 'X-Api-Key'  # Match the case you're using in the client 