from django.core.management.base import BaseCommand
from api.models.google_calendar import GoogleCalendarCredentials
import json

class Command(BaseCommand):
    help = 'Debug credentials in the database'

    def handle(self, *args, **options):
        creds = GoogleCalendarCredentials.objects.all()
        self.stdout.write(f"Found {creds.count()} credentials")
        
        for cred in creds:
            self.stdout.write(f"\nCredential ID: {cred.id}")
            self.stdout.write(f"Email: {cred.email}")
            self.stdout.write(f"Type of credentials: {type(cred.credentials)}")
            
            try:
                # Use the model's decryption method
                decrypted_creds = cred.get_credentials()
                self.stdout.write("\nDecrypted credentials:")
                self.stdout.write(json.dumps(decrypted_creds, indent=2))
                
                # Validate required fields
                required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes']
                missing_fields = [field for field in required_fields if field not in decrypted_creds]
                
                if missing_fields:
                    self.stdout.write("\nWARNING: Missing required fields:")
                    self.stdout.write(", ".join(missing_fields))
                else:
                    self.stdout.write("\nAll required fields present ✓")
                    
            except Exception as e:
                self.stdout.write(f"\nError decrypting credentials: {str(e)}") 