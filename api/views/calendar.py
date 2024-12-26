import os
from api.utils.auth import admin_required
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from ..models.google_calendar import GoogleCalendarCredentials
from ..utils.google_calendar import GoogleCalendarService
from datetime import datetime, timedelta
from django.utils import timezone
import json
from googleapiclient.discovery import build
from django.contrib.auth.models import User
from django.conf import settings
from ..serializers.calendar import BookMeetingSerializer
import logging

class CalendarViewSet(viewsets.ViewSet):
    """
    ViewSet for handling all calendar-related operations
    """
    
    @action(detail=False, methods=['get'], url_path='auth')
    @admin_required
    def auth_calendar(self, request):
        """Start OAuth flow for Google Calendar"""
        try:
            flow = GoogleCalendarService.create_flow()
            # Add trailing slash to match Google's error message
            redirect_uri = 'https://api.materials.nyc/api/calendar/oauth2callback/'
            flow.redirect_uri = redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                prompt='consent'
            )
            request.session['google_oauth_state'] = state
            return Response({'authorization_url': authorization_url})
        except Exception as e:
            logger = logging.getLogger('api')
            logger.error(f"Error in auth_calendar: {str(e)}")
            return Response({
                'error': 'Failed to start OAuth flow',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='oauth2callback', 
            authentication_classes=[], permission_classes=[])
    def oauth2callback(self, request):
        """Handle OAuth callback from Google"""
        logger = logging.getLogger('api')
        try:
            state = request.session.get('google_oauth_state')
            logger.debug(f"OAuth state from session: {state}")
            
            flow = GoogleCalendarService.create_flow()
            # Add trailing slash here too
            flow.redirect_uri = 'https://api.materials.nyc/api/calendar/oauth2callback/'
            
            flow.fetch_token(
                authorization_response=request.build_absolute_uri(),
                state=state
            )
            
            credentials = flow.credentials
            
            # Use the flow's credentials to build the service
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            email = user_info.get('email')
            logger.debug(f"Got user email: {email}")

            # Get Calendar ID
            calendar_service = build('calendar', 'v3', credentials=credentials)
            calendar_list = calendar_service.calendarList().list().execute()
            primary_calendar = next(
                (cal for cal in calendar_list.get('items', []) if cal.get('primary')),
                None
            )
            
            if not primary_calendar:
                logger.error("No primary calendar found")
                return Response(
                    {'error': 'No primary calendar found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            calendar_id = primary_calendar['id']
            logger.debug(f"Got calendar ID: {calendar_id}")

            # Create or get a user based on the Google email
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'is_active': True
                }
            )
            logger.debug(f"User {'created' if created else 'retrieved'}: {user.username}")

            # Convert credentials to dict
            creds_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': list(credentials.scopes)  # Convert set to list for JSON serialization
            }

            try:
                calendar_creds, created = GoogleCalendarCredentials.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={
                        'calendar_id': calendar_id,
                        'is_primary': not GoogleCalendarCredentials.objects.filter(user=user).exists()
                    }
                )
                
                # Use the model's set_credentials method to properly encrypt
                calendar_creds.set_credentials(creds_dict)
                calendar_creds.save()
                
            except Exception as e:
                logger.error(f"Error saving credentials: {str(e)}")
                raise
            
            return Response({
                'message': 'Calendar connected successfully',
                'email': email,
                'is_primary': calendar_creds.is_primary,
                'user_id': user.id,
                'calendar_id': calendar_id
            })
        except Exception as e:
            logger.error(f"Error in oauth2callback: {str(e)}")
            return Response({
                'error': 'Failed to handle OAuth callback',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='set-primary')
    def set_primary_calendar(self, request):
        """Set a calendar as primary"""
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            calendar_creds = GoogleCalendarCredentials.objects.get(
                user=request.user,
                email=email
            )
            calendar_creds.is_primary = True
            calendar_creds.save()
            return Response({
                'message': f'Calendar {email} set as primary',
                'email': email
            })
        except GoogleCalendarCredentials.DoesNotExist:
            return Response(
                {'error': f'Calendar with email {email} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='availability')
    def get_availability(self, request):
        """Get availability for a specific calendar"""
        email = request.query_params.get('email')
        try:
            if email:
                calendar_creds = GoogleCalendarCredentials.objects.get(
                    user=request.user,
                    email=email
                )
            else:
                # If no email specified, use primary calendar
                calendar_creds = GoogleCalendarCredentials.objects.get(
                    user=request.user,
                    is_primary=True
                )
            
            service = GoogleCalendarService.build_service(calendar_creds.credentials)
            days = int(request.query_params.get('days', 7))
            events = GoogleCalendarService.get_availability(service, calendar_creds.calendar_id, days)
            
            return Response({
                'email': calendar_creds.email,
                'is_primary': calendar_creds.is_primary,
                'events': events
            })
        except GoogleCalendarCredentials.DoesNotExist:
            return Response(
                {'error': 'Calendar not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], url_path='book')
    def book_meeting(self, request):
        """Book a meeting on the primary calendar"""
        # Check API key
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != settings.API_KEY:
            return Response({
                'error': 'Invalid or missing API key'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Validate request data
        serializer = BookMeetingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get any primary calendar in the system
            calendar_creds = GoogleCalendarCredentials.objects.get(is_primary=True)
            service = GoogleCalendarService.build_service(
                calendar_creds.credentials,
                calendar_creds=None
            )
            
            validated_data = serializer.validated_data
            
            event = GoogleCalendarService.create_event(
                service,
                calendar_creds.calendar_id,
                validated_data['start_time'],
                validated_data['end_time'],
                validated_data['summary'],
                validated_data.get('description'),
                validated_data.get('attendees', [])
            )
            
            return Response({
                'message': 'Event created successfully',
                'event': event,
                'calendar': calendar_creds.email,
                'duration_minutes': validated_data['duration_minutes']
            })
        except GoogleCalendarCredentials.DoesNotExist:
            return Response(
                {'error': 'No primary calendar set in the system'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create event: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='all-availability')
    def get_all_availability(self, request):
        """Get free time slots across all calendars"""
        logger = logging.getLogger('api')
        days = int(request.query_params.get('days', 7))
        
        calendars = GoogleCalendarCredentials.objects.select_related('user').all()
        logger.info(f"Found {calendars.count()} total calendars in the system")
        
        # Get current time rounded to the next hour
        now = timezone.now()
        current_time = now.replace(minute=0, second=0, microsecond=0)
        if now.minute > 0:
            current_time = current_time + timedelta(hours=1)
        
        # Create time slots for the next 7 days (9 AM to 5 PM)
        time_slots = []
        for day in range(days):
            day_start = current_time + timedelta(days=day)
            day_start = day_start.replace(hour=9)  # Start at 9 AM
            
            # Create hourly slots from 9 AM to 5 PM
            for hour in range(9, 17):  # 9 AM to 4 PM (last slot will be 4-5 PM)
                slot_start = day_start.replace(hour=hour)
                slot_end = slot_start + timedelta(hours=1)
                time_slots.append((slot_start, slot_end))
        
        # Collect all busy periods
        busy_periods = []
        for cal in calendars:
            try:
                logger.info(f"Processing calendar: {cal.email} (ID: {cal.id})")
                
                creds_dict = cal.get_credentials()
                service = GoogleCalendarService.build_service(creds_dict)
                
                events = GoogleCalendarService.get_availability(
                    service, 
                    cal.calendar_id, 
                    days
                )
                
                for event in events:
                    start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    if start.tzinfo is None:
                        start = timezone.make_aware(start)
                        
                    end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
                    if end.tzinfo is None:
                        end = timezone.make_aware(end)
                        
                    busy_periods.append((start, end))
                
                logger.info(f"Added {len(events)} events from {cal.email}")
                
            except Exception as e:
                logger.error(f"Error getting availability for calendar {cal.email}: {str(e)}")
                logger.exception(e)
        
        # Find available slots
        available_slots = []
        for slot_start, slot_end in time_slots:
            is_available = True
            
            for busy_start, busy_end in busy_periods:
                # Check if this slot overlaps with any busy period
                if (slot_start < busy_end and slot_end > busy_start):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start': slot_start.isoformat(),
                    'end': slot_end.isoformat(),
                    'duration_minutes': 60
                })
        
        return Response({
            'available_slots': available_slots,
            'total_slots': len(available_slots),
            'calendars_processed': len(calendars),
            'time_zone': str(timezone.get_current_timezone())
        })

    @action(detail=False, methods=['get'], url_path='events')
    @admin_required
    def get_all_events(self, request):
        """Get all events from all calendars"""
        logger = logging.getLogger('api')
        
        days = int(request.query_params.get('days', 7))
        events_list = []
        calendars = GoogleCalendarCredentials.objects.all()
        
        for creds in calendars:
            try:
                # Log the raw credentials for debugging
                logger.debug(f"Raw credentials for {creds.email}: {creds.credentials}")
                
                # Get and validate credentials
                credentials = creds.get_credentials()
                if not credentials:
                    raise ValueError("No valid credentials found")
                
                service = GoogleCalendarService.build_service(credentials)
                
                events = GoogleCalendarService.get_events(
                    service, 
                    creds.calendar_id, 
                    days
                )
                
                events_list.append({
                    'email': creds.email,
                    'is_primary': creds.is_primary,
                    'events': events,
                    'calendar_id': creds.calendar_id,
                    'user': creds.user.username
                })
                
            except Exception as e:
                logger.error(f"Error processing calendar {creds.email}: {str(e)}")
                events_list.append({
                    'email': creds.email,
                    'is_primary': creds.is_primary,
                    'error': f"Failed to process calendar: {str(e)}",
                    'calendar_id': creds.calendar_id,
                    'user': creds.user.username
                })

        return Response({
            'calendars_found': len(calendars),
            'calendars': events_list
        }) 