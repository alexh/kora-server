from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from django.conf import settings
import json

class GoogleCalendarService:
    @staticmethod
    def create_flow():
        """Create OAuth2 flow for Google Calendar"""
        flow = Flow.from_client_config(
            settings.GOOGLE_OAUTH_CONFIG,
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.events',
                'https://www.googleapis.com/auth/calendar.readonly',
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
            ]
        )
        flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
        return flow

    @staticmethod
    def build_service(creds_dict):
        """Build Google Calendar service from credentials"""
        # Ensure we're working with a dictionary
        if not isinstance(creds_dict, dict):
            try:
                if isinstance(creds_dict, (bytes, memoryview)):
                    creds_dict = json.loads(creds_dict.tobytes().decode('utf-8'))
                elif isinstance(creds_dict, str):
                    creds_dict = json.loads(creds_dict)
                else:
                    raise ValueError(f"Unexpected credentials type: {type(creds_dict)}")
            except Exception as e:
                raise ValueError(f"Failed to parse credentials: {str(e)}")

        # Ensure all required fields are present
        required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes']
        missing_fields = [field for field in required_fields if field not in creds_dict]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Create credentials object
        try:
            credentials = Credentials(
                token=str(creds_dict['token']),  # Ensure token is string
                refresh_token=str(creds_dict['refresh_token']),
                token_uri=str(creds_dict['token_uri']),
                client_id=str(creds_dict['client_id']),
                client_secret=str(creds_dict['client_secret']),
                scopes=creds_dict['scopes']
            )
        except Exception as e:
            raise ValueError(f"Failed to create credentials object: {str(e)}")

        # Build and return service
        return build('calendar', 'v3', credentials=credentials)

    @staticmethod
    def get_availability(service, calendar_id, days=7):
        """Get free/busy information for calendar"""
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days)
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        availability = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            availability.append({
                'start': start,
                'end': end,
                'summary': event.get('summary', 'Busy'),
                'id': event['id']
            })
            
        return availability

    @staticmethod
    def get_events(service, calendar_id, days=7):
        """Get raw event data from calendar"""
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days)
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])

    @staticmethod
    def create_event(service, calendar_id, start_time, end_time, summary, description=None, attendees=None):
        """Create a new event on the calendar"""
        event = {
            'summary': summary,
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()},
        }
        
        if description:
            event['description'] = description
            
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
            
        return service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute() 