from rest_framework import viewsets
from rest_framework.response import Response
from ..models import Issue
from ..serializers.issue import IssueSerializer
from api.utils import admin_required, send_discord_webhook
import logging

logger = logging.getLogger(__name__)

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    
    @admin_required
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Save the issue
        issue = serializer.save()
        
        logger.info("New issue created with severity: %s", issue.severity)
        
        # Send Discord notification
        try:
            # Get severity emoji
            severity_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🟠',
                'CRITICAL': '🔴'
            }.get(issue.severity, '❓')

            fields = [
                {
                    "name": f"{severity_emoji} Severity",
                    "value": issue.severity.title(),
                    "inline": True
                },
                {
                    "name": "📝 Description",
                    "value": (issue.description[:1000] + "...") 
                        if len(issue.description) > 1000 
                        else issue.description,
                    "inline": False
                },
                {
                    "name": "⏰ Timestamp",
                    "value": issue.timestamp.strftime("%Y-%m-%d %I:%M %p"),
                    "inline": True
                }
            ]

            # Add contact information if provided
            if issue.customer_email:
                fields.append({
                    "name": "📧 Customer Email",
                    "value": issue.customer_email,
                    "inline": True
                })

            if issue.customer_phone:
                fields.append({
                    "name": "📞 Customer Phone",
                    "value": issue.customer_phone,
                    "inline": True
                })

            # Set color based on severity
            colors = {
                'LOW': '2ecc71',      # Green
                'MEDIUM': 'f1c40f',   # Yellow
                'HIGH': 'e67e22',     # Orange
                'CRITICAL': 'e74c3c'  # Red
            }
            color = colors.get(issue.severity, '95a5a6')  # Default gray

            send_discord_webhook(
                title=f"{severity_emoji} New Issue Reported",
                description=f"A new {issue.severity.lower()} severity issue has been reported.",
                fields=fields,
                color=color,
                username="Issue Tracker",
                footer_text="Issue Management System",
                timestamp=True
            )
            logger.info("Discord notification sent for new issue")
            
        except Exception as webhook_error:
            logger.error("Failed to send Discord notification for new issue: %s", str(webhook_error))
            # Continue execution even if webhook fails 