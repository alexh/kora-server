from rest_framework.permissions import BasePermission

class HasValidAPIKey(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth)  # auth will be True if APIKeyAuthentication succeeded 