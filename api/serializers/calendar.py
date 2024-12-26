from rest_framework import serializers
from datetime import datetime, timedelta

class BookMeetingSerializer(serializers.Serializer):
    start_time = serializers.CharField(help_text="ISO format datetime string (e.g., '2024-02-26T14:00:00Z')")
    duration_minutes = serializers.IntegerField(
        default=60,
        min_value=15,
        max_value=480,  # 8 hours max
        help_text="Duration in minutes (15-480)"
    )
    summary = serializers.CharField(
        max_length=200,
        help_text="Meeting title"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Meeting description (optional)"
    )
    attendees = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list,
        help_text="List of attendee email addresses"
    )

    def validate_start_time(self, value):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid datetime format. Use ISO format (e.g., '2024-02-26T14:00:00Z')")

    def validate(self, data):
        start_time = data['start_time']
        duration = data['duration_minutes']
        
        # Check if start time is in the past
        if start_time < datetime.now(start_time.tzinfo):
            raise serializers.ValidationError("Start time cannot be in the past")
        
        # Add end_time to the validated data
        data['end_time'] = start_time + timedelta(minutes=duration)
        
        return data 