import os
import logging
import shopify

logger = logging.getLogger(__name__)

def init_shopify():
    shop_url = os.getenv('SHOPIFY_SHOP_URL')
    if not shop_url.endswith('.myshopify.com'):
        shop_url = f"{shop_url}.myshopify.com"
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

    if not shop_url or not access_token:
        raise ValueError(
            f"Missing Shopify credentials: \n"
            f"SHOPIFY_SHOP_URL: {'✓' if shop_url else '✗'}\n"
            f"SHOPIFY_ACCESS_TOKEN: {'✓' if access_token else '✗'}"
        )

    logger.info(f"Initializing Shopify session with shop URL: {shop_url}")
    try:
        session = shopify.Session(shop_url, '2023-04', access_token)
        shopify.ShopifyResource.activate_session(session)
        logger.info("Shopify session initialized successfully")
    except Exception as e:
        error_msg = f"Failed to initialize Shopify session: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) 