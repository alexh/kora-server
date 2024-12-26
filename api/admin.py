from django.contrib import admin
from .models.google_calendar import GoogleCalendarCredentials
import json

class GoogleCalendarCredentialsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_primary', 'calendar_id', 'created_at')
    list_filter = ('is_primary',)
    search_fields = ('user__email', 'email')
    readonly_fields = ('email', 'calendar_id', 'created_at', 'updated_at', 'formatted_credentials')
    exclude = ('credentials',)

    def formatted_credentials(self, obj):
        """Format decrypted credentials for display"""
        try:
            creds = obj.get_credentials()
            return json.dumps(creds, indent=2)
        except Exception as e:
            return f"Error decrypting credentials: {str(e)}"
    formatted_credentials.short_description = 'Credentials'

    def has_add_permission(self, request):
        """Disable adding new credentials through admin"""
        return False

    def get_fields(self, request, obj=None):
        return ('user', 'email', 'is_primary', 'calendar_id', 'formatted_credentials', 'created_at', 'updated_at')

admin.site.register(GoogleCalendarCredentials, GoogleCalendarCredentialsAdmin)

# Customize admin site header and title
admin.site.site_header = 'UMI Administration'
admin.site.site_title = 'UMI Admin Portal'
admin.site.index_title = 'Welcome to UMI Admin Portal' 