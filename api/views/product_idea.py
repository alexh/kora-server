from rest_framework import viewsets
from rest_framework.response import Response
from ..models import ProductIdea
from ..serializers.product_idea import ProductIdeaSerializer
from api.utils import admin_required, send_discord_webhook
import logging

logger = logging.getLogger(__name__)

class ProductIdeaViewSet(viewsets.ModelViewSet):
    queryset = ProductIdea.objects.all()
    serializer_class = ProductIdeaSerializer
    
    @admin_required
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Save the product idea
        product_idea = serializer.save()
        
        logger.info("New product idea created: %s", product_idea.title)
        
        # Send Discord notification
        try:
            fields = [
                {
                    "name": "💡 Title",
                    "value": product_idea.title,
                    "inline": False
                },
                {
                    "name": "📝 Description",
                    "value": (product_idea.description[:1000] + "...") 
                        if len(product_idea.description) > 1000 
                        else product_idea.description,
                    "inline": False
                },
                {
                    "name": "⏰ Created At",
                    "value": product_idea.created_at.strftime("%Y-%m-%d %I:%M %p"),
                    "inline": True
                }
            ]

            send_discord_webhook(
                title="💡 New Product Idea Submitted",
                description="A new product idea has been added to the system.",
                fields=fields,
                color="5865F2",  # Discord blue
                username="Product Development",
                footer_text="Product Ideas Manager",
                timestamp=True
            )
            logger.info("Discord notification sent for new product idea")
            
        except Exception as webhook_error:
            logger.error("Failed to send Discord notification for new product idea: %s", str(webhook_error))
            # Continue execution even if webhook fails 