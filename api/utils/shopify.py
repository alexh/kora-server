import os
import logging
from django.conf import settings
import shopify

logger = logging.getLogger(__name__)

def init_shopify():
    """Initialize Shopify API connection"""
    shop_url = settings.SHOPIFY_SHOP_URL
    if not shop_url.endswith('.myshopify.com'):
        shop_url = f"{shop_url}.myshopify.com"
    access_token = settings.SHOPIFY_ACCESS_TOKEN

    if not shop_url or not access_token:
        raise ValueError("SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN must be set")

    logger.info(f"Initializing Shopify session with shop URL: {shop_url}")
    try:
        session = shopify.Session(shop_url, '2023-04', access_token)
        shopify.ShopifyResource.activate_session(session)
        logger.info("Shopify session initialized successfully")
    except Exception as e:
        error_msg = f"Failed to initialize Shopify session: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)