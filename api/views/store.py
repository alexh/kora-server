from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
import shopify
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

def init_shopify():
    """Initialize Shopify API client"""
    # Debug logging
    logger.info(f"Environment SHOPIFY_SHOP_URL: {os.getenv('SHOPIFY_SHOP_URL')}")
    logger.info(f"Environment SHOPIFY_ACCESS_TOKEN: {os.getenv('SHOPIFY_ACCESS_TOKEN')}")
    logger.info(f"Settings SHOPIFY_SHOP_URL: {settings.SHOPIFY_SHOP_URL}")
    logger.info(f"Settings SHOPIFY_ACCESS_TOKEN: {settings.SHOPIFY_ACCESS_TOKEN}")

    shop_url = settings.SHOPIFY_SHOP_URL
    access_token = settings.SHOPIFY_ACCESS_TOKEN

    if not shop_url or not access_token:
        raise ValueError(f"SHOPIFY_SHOP_URL ({shop_url}) and SHOPIFY_ACCESS_TOKEN ({access_token}) must be set")

    # Format the shop URL for the API
    if '.myshopify.com' not in shop_url:
        shop_url = f"{shop_url}.myshopify.com"
    if not shop_url.startswith('https://'):
        shop_url = f'https://{shop_url}'

    # Set up the Shopify API client
    shopify.ShopifyResource.site = f"{shop_url}/admin/api/2023-04"
    shopify.ShopifyResource.headers = {'X-Shopify-Access-Token': access_token}

class ProductViewSet(viewsets.ViewSet):
    basename = 'products'
    
    def get_shopify_client(self):
        """Initialize Shopify API client"""
        shop_url = settings.SHOPIFY_SHOP_URL
        access_token = settings.SHOPIFY_ACCESS_TOKEN

        if not shop_url or not access_token:
            raise ValueError("SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN must be set")

        # Format the shop URL for the API
        if '.myshopify.com' not in shop_url:
            shop_url = f"{shop_url}.myshopify.com"
        if not shop_url.startswith('https://'):
            shop_url = f'https://{shop_url}'

        # Set up the Shopify API client
        shopify.ShopifyResource.site = f"{shop_url}/admin/api/2023-04"
        shopify.ShopifyResource.headers = {'X-Shopify-Access-Token': access_token}

    def list(self, request):
        """Get all products"""
        try:
            self.get_shopify_client()
            
            # Try to get from cache first
            cache_key = 'shopify_products'
            cached_products = cache.get(cache_key)
            
            if cached_products:
                return Response({"products": cached_products, "source": "cache"})
            
            # If not in cache, fetch from Shopify
            products = shopify.Product.find(status='active')
            product_list = []
            
            for product in products:
                variants = []
                for variant in product.variants:
                    variants.append({
                        "id": variant.id,
                        "title": variant.title,
                        "sku": variant.sku,
                        "price": variant.price,
                        "compare_at_price": variant.compare_at_price,
                        "in_stock": variant.inventory_quantity > 0,
                        "inventory_quantity": variant.inventory_quantity,
                        "requires_shipping": variant.requires_shipping
                    })
                
                product_list.append({
                    "id": product.id,
                    "title": product.title,
                    "description": product.body_html,
                    "vendor": product.vendor,
                    "product_type": product.product_type,
                    "tags": product.tags.split(',') if product.tags else [],
                    "handle": product.handle,
                    "published_at": product.published_at,
                    "variants": variants,
                    "has_stock": any(v["in_stock"] for v in variants),
                    "url": f"https://materials.nyc/products/{product.handle}"
                })
            
            # Store in cache for 5 minutes
            cache.set(cache_key, product_list, timeout=300)
            
            return Response({"products": product_list, "source": "shopify"})
        except Exception as e:
            logger.error(f"Shopify API error: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        try:
            init_shopify()  # Initialize Shopify before making API calls
            
            email = request.query_params.get('email')
            phone = request.query_params.get('phone')

            if not email and not phone:
                raise ValidationError("Either email or phone number must be provided")

            # Remove '#' from order number if present
            order_number = pk.replace('#', '')
            
            # Search for orders
            orders = shopify.Order.find(name=f"#{order_number}", status="any")
            
            # Find the order that matches either email or phone
            matching_order = None
            for order in orders:
                order_phone = ''.join(filter(str.isdigit, order.phone or ''))
                query_phone = ''.join(filter(str.isdigit, phone or ''))
                
                if (email and order.email and order.email.lower() == email.lower()) or \
                   (phone and order_phone and order_phone.endswith(query_phone)):
                    matching_order = order
                    break
            
            if not matching_order:
                return Response(
                    {"detail": "No order found matching this order number and contact information"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Format line items (without personal info)
            line_items = []
            for item in matching_order.line_items:
                line_items.append({
                    "title": item.title,
                    "quantity": item.quantity,
                    "variant_title": item.variant_title
                })
            
            return Response({
                "order_number": matching_order.name,
                "created_at": matching_order.created_at,
                "status": matching_order.financial_status,
                "fulfillment_status": matching_order.fulfillment_status,
                "line_items": line_items
            })
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request):
        try:
            init_shopify()  # Initialize Shopify before making API calls
            
            email = request.query_params.get('email')
            phone = request.query_params.get('phone')

            if not email and not phone:
                raise ValidationError("Either email or phone number must be provided")
            
            # Find orders for this customer
            orders = shopify.Order.find(status="any", limit=5)  # Last 5 orders
            
            matching_orders = []
            for order in orders:
                order_phone = ''.join(filter(str.isdigit, order.phone or ''))
                query_phone = ''.join(filter(str.isdigit, phone or ''))
                
                if (email and order.email and order.email.lower() == email.lower()) or \
                   (phone and order_phone and order_phone.endswith(query_phone)):
                    # Calculate total items by summing quantities
                    total_items = sum(item.quantity for item in order.line_items)
                    
                    matching_orders.append({
                        "order_number": order.name,
                        "created_at": order.created_at,
                        "status": order.financial_status,
                        "fulfillment_status": order.fulfillment_status,
                        "total_items": total_items
                    })
            
            return Response({"orders": matching_orders})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 