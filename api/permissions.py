from rest_framework.permissions import BasePermission
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class HasValidAPIKey(BasePermission):
    def has_permission(self, request, view):
        api_key = (
            request.META.get('HTTP_X_API_KEY') or
            request.META.get('HTTP_X_Api_Key') or
            request.META.get('HTTP_X_API_KEY') or
            request.META.get('HTTP_X_Api_key') or
            request.headers.get('X-API-Key') or
            request.headers.get('x-api-key')
        )
        
        if not api_key:
            logger.warning("No API key provided")
            return False
            
        # Check if this view allows demo keys
        allows_demo = getattr(view, 'allows_demo_keys', False)
        logger.debug(f"Checking permissions for {view.__class__.__name__}")
        
        if allows_demo and api_key in settings.DEMO_API_KEYS:
            logger.info(f"Demo access granted for {view.__class__.__name__}")
            return True
            
        is_valid = api_key == settings.API_KEY
        if not is_valid:
            logger.warning("Invalid API key")
        return is_valid 