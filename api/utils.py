from rest_framework.views import exception_handler
import logging
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from discord_webhook import DiscordWebhook
from discord_webhook import DiscordEmbed

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Log the error
    logger.error(f"Exception occurred: {exc}")
    logger.error(f"Context: {context}")
    
    # Call REST framework's default exception handler
    response = exception_handler(exc, context)
    
    # Add more error details if in debug mode
    if response is not None:
        response.data['status_code'] = response.status_code
        
    return response 

def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        # Get the actual request object
        request = getattr(request, '_request', request)
        
        admin_key = (
            request.headers.get('X-Admin-Key') or
            request.headers.get('x-admin-key') or
            request.META.get('HTTP_X_ADMIN_KEY')
        )
        
        if not admin_key or admin_key != settings.ADMIN_API_KEY:
            return JsonResponse(
                {'error': 'Unauthorized - Invalid or missing X-Admin-Key header'}, 
                status=401
            )
        return view_func(self, request, *args, **kwargs)
    return wrapped_view 

def send_discord_webhook(
    message=None, 
    title=None,
    description=None,
    fields=None,
    color=None,
    username=None,
    avatar_url=None,
    thumbnail_url=None,
    image_url=None,
    footer_text=None,
    footer_icon=None,
    author_name=None,
    author_url=None,
    author_icon=None,
    timestamp=True
):
    """
    Send a Discord webhook with rich formatting options.
    
    Args:
        message (str, optional): Simple message content
        title (str, optional): Embed title
        description (str, optional): Embed description
        fields (list, optional): List of dicts with name, value, and inline keys
        color (str, optional): Hex color code for embed (without #)
        username (str, optional): Webhook username
        avatar_url (str, optional): URL for webhook avatar
        thumbnail_url (str, optional): URL for embed thumbnail
        image_url (str, optional): URL for large embed image
        footer_text (str, optional): Footer text
        footer_icon (str, optional): URL for footer icon
        author_name (str, optional): Author name
        author_url (str, optional): Author URL
        author_icon (str, optional): URL for author icon
        timestamp (bool, optional): Whether to include timestamp
    """
    webhook = DiscordWebhook(
        url=settings.DISCORD_WEBHOOK_URL,
        # username=username,
        # avatar_url=avatar_url,
        content=message
    )

    logger.info(f"Sending Discord webhook with message: {message}")

    # Create embed if any embed-specific parameters are provided
    if any([title, description, fields, color, thumbnail_url, image_url,
            footer_text, author_name]):
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=color
        )

        # Add fields
        if fields:
            for field in fields:
                embed.add_embed_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', True)
                )

        # Add author if provided
        if author_name:
            embed.set_author(
                name=author_name,
                url=author_url,
                icon_url=author_icon
            )

        # Add footer if provided
        if footer_text:
            embed.set_footer(
                text=footer_text,
                icon_url=footer_icon
            )

        # Add images if provided
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if image_url:
            embed.set_image(url=image_url)

        # Add timestamp if enabled
        if timestamp:
            embed.set_timestamp()

        webhook.add_embed(embed)

    try:
        logger.info(f"Sending Discord webhook with message: {message}")
        response = webhook.execute()
        logger.info(f"Discord webhook sent successfully: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send Discord webhook: {str(e)}")
        raise