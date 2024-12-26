from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import json

class GoogleCalendarCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    credentials = models.BinaryField()  # Store encrypted data as binary
    is_primary = models.BooleanField(default=False)
    calendar_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Google Calendar Credentials'
        verbose_name_plural = 'Google Calendar Credentials'
        unique_together = [['user', 'email']]

    def __str__(self):
        return f"{self.email} ({'Primary' if self.is_primary else 'Secondary'})"

    @property
    def _fernet(self):
        key = settings.ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)

    def get_credentials(self):
        """Decrypt and return credentials as dict"""
        if not self.credentials:
            return {}
            
        # Convert memoryview to bytes if needed
        if isinstance(self.credentials, memoryview):
            encrypted_data = self.credentials.tobytes()
        else:
            encrypted_data = self.credentials
            
        try:
            decrypted = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted)
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")

    def set_credentials(self, creds_dict):
        """Encrypt and store credentials"""
        if isinstance(creds_dict, (str, bytes)):
            creds_json = creds_dict
        else:
            creds_json = json.dumps(creds_dict)
            
        # Ensure we're working with bytes
        if isinstance(creds_json, str):
            creds_json = creds_json.encode()
            
        self.credentials = self._fernet.encrypt(creds_json)

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other calendars for this user as non-primary
            GoogleCalendarCredentials.objects.filter(
                user=self.user
            ).exclude(id=self.id).update(is_primary=False)
            
        super().save(*args, **kwargs) 