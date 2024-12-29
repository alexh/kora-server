from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
import shopify
from rest_framework.exceptions import ValidationError
import logging
import traceback
import sys
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from api.utils.utils import send_discord_webhook
from api.utils.shopify import init_shopify
from api.utils.auth import allow_demo_key
from api.permissions import HasValidAPIKey

logger = logging.getLogger(__name__)

def format_exception():
    """Format the current exception info into a detailed string"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    trace_parts = traceback.extract_tb(exc_traceback)
    
    # Format into readable strings
    trace_strings = []
    for filename, line, func, text in trace_parts:
        trace_strings.append(f"File {filename}, line {line}, in {func}")
        if text:
            trace_strings.append(f"  {text}")
    
    return {
        'error': str(exc_value),
        'type': exc_type.__name__,
        'trace': trace_strings,
    }

def fetch_tracking_status(url):
    """Fetch the content from a tracking URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Get the page content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return {
            'url': url,
            'status_code': response.status_code,
            'content': soup.get_text()[:1000],  # First 1000 chars of text content
            'raw_html': response.text if settings.DEBUG else None  # Only include raw HTML in debug mode
        }
    except Exception as e:
        logger.error(f"Error fetching tracking status for {url}: {str(e)}")
        return {
            'url': url,
            'error': str(e),
            'status_code': getattr(response, 'status_code', None) if 'response' in locals() else None
        }

class StoreViewSet(viewsets.ViewSet):
    permission_classes = [HasValidAPIKey]
    allows_demo_keys = True
    
    @action(detail=False, methods=['get'], url_path='products')
    def products(self, request):
        """List all products"""
        return self.get_products(request)

    def get_products(self, request):
        """List all products implementation"""
        try:
            logger.info("🚀 STARTING NEW PRODUCT FETCH REQUEST 🚀")
            
            # Initialize Shopify API first
            init_shopify()
            
            cache_key = 'shopify_products'
            cached_products = cache.get(cache_key)
            
            if cached_products:
                logger.info("💾 CACHE HIT - Returning %d products", len(cached_products))
                return Response({"products": cached_products, "source": "cache"})
            
            logger.info("🔄 CACHE MISS - Fetching fresh data from Shopify")
            products = shopify.Product.find(status='active')
            product_list = []
            
            total_products = len(products)
            total_variants = 0
            out_of_stock_products = 0
            low_stock_products = []

            logger.info("📦 Processing %d products from Shopify", total_products)

            for product in products:
                variants = []
                for variant in product.variants:
                    inventory_qty = variant.inventory_quantity
                    variants.append({
                        "id": variant.id,
                        "title": variant.title,
                        "sku": variant.sku,
                        "price": variant.price,
                        "compare_at_price": variant.compare_at_price,
                        "in_stock": inventory_qty > 0,
                        "inventory_quantity": inventory_qty,
                        "requires_shipping": variant.requires_shipping
                    })
                    
                    if inventory_qty == 0:
                        logger.debug("❌ Variant '%s' of '%s' is out of stock", 
                                   variant.title, product.title)
                    elif inventory_qty <= 5:
                        logger.debug("⚠️ Variant '%s' of '%s' has low stock (%d units)", 
                                   variant.title, product.title, inventory_qty)

                product_has_stock = any(v["in_stock"] for v in variants)
                if not product_has_stock:
                    out_of_stock_products += 1
                    logger.info("🚫 Product '%s' is completely out of stock", product.title)
                elif any(0 < v["inventory_quantity"] <= 5 for v in variants):
                    low_stock_products.append(product.title)
                    logger.info("📉 Product '%s' has low stock variants", product.title)
                
                total_variants += len(variants)
                
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
                    "has_stock": product_has_stock,
                    "url": f"https://utility.materials.nyc/products/{product.handle}"
                })

            logger.info(
                "📊 INVENTORY SUMMARY:\n"
                "- Total Products: %d\n"
                "- Total Variants: %d\n"
                "- Out of Stock: %d\n"
                "- Low Stock: %d",
                total_products, total_variants, out_of_stock_products, len(low_stock_products)
            )

            if low_stock_products:
                logger.info("📋 Low stock products:\n%s", 
                           "\n".join(f"- {product}" for product in low_stock_products))

            # Store in cache for 5 minutes
            cache.set(cache_key, product_list, timeout=300)
            logger.info("💾 Products cached successfully (expires in 5 minutes)")


            logger.info("📨 Sending inventory update to Discord")
            
            # Format low stock products list (limited to 5 for readability)
            low_stock_field = {
                "name": "📉 Low Stock Products",
                "value": "\n".join(f"• {product}" for product in low_stock_products[:5]),
                "inline": False
            } if low_stock_products else None

            fields = [
                {
                    "name": "📦 Total Products",
                    "value": str(total_products),
                    "inline": True
                },
                {
                    "name": "🔢 Total Variants",
                    "value": str(total_variants),
                    "inline": True
                },
                {
                    "name": "❌ Out of Stock",
                    "value": f"{out_of_stock_products} products",
                    "inline": True
                },
                {
                    "name": "⚠️ Low Stock",
                    "value": f"{len(low_stock_products)} products",
                    "inline": True
                },
                {
                    "name": "💾 Cache Status",
                    "value": "✅ Updated (5min)",
                    "inline": True
                }
            ]

            # Add low stock field if there are any
            if low_stock_field:
                fields.append(low_stock_field)

            # Add note if there are more low stock products
            if len(low_stock_products) > 5:
                fields.append({
                    "name": "📝 Note",
                    "value": f"_{len(low_stock_products) - 5} more products have low stock_",
                    "inline": False
                })

            send_discord_webhook(
                title="⚙️ utility.materials.nyc Inventory Update",
                description="Latest product catalog refresh completed",
                fields=fields,
                color="ff5f05",  # Orange color
                timestamp=True
            )
            logger.info("✅ Discord notification sent successfully")
        
            return Response({"products": product_list, "source": "shopify"})
            
        except Exception as e:
            error_details = format_exception()
            logger.error("❌ Error fetching products: %s", error_details)
            
            if settings.DEBUG:
                return Response(error_details, status=500)
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='orders/(?P<order_number>[^/.]+)')
    def lookup_order(self, request, order_number=None):
        """Look up a specific order by number"""
        email = request.query_params.get('email')
        phone = request.query_params.get('phone')

        if not email and not phone:
            raise ValidationError("Either email or phone number must be provided")

        try:
            # Remove '#' from order number if present
            order_number = order_number.replace('#', '')
            
            init_shopify()
            orders = shopify.Order.find(
                name=f"#{order_number}",
                status="any"
            )
            
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
                    {"error": "No order found matching this order number and contact information"},
                    status=404
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
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            error_details = format_exception()
            logger.error(f"Error looking up order: {error_details}")
            
            if settings.DEBUG:
                return Response(error_details, status=500)
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def orders(self, request):
        """Get all orders for a customer"""
        email = request.query_params.get('email')
        phone = request.query_params.get('phone')

        if not email and not phone:
            raise ValidationError("Either email or phone number must be provided")
        
        try:
            init_shopify()
            
            query_params = {'status': 'any', 'limit': 250}
            if email:
                query_params['email'] = email
            
            orders = shopify.Order.find(**query_params)
            
            matching_orders = []
            for order in orders:
                order_phone = ''.join(filter(str.isdigit, order.phone or ''))
                query_phone = ''.join(filter(str.isdigit, phone or ''))
                
                if (email and order.email and order.email.lower() == email.lower()) or \
                   (phone and order_phone and order_phone.endswith(query_phone)):
                    total_items = sum(item.quantity for item in order.line_items)
                    
                    # Get tracking numbers from fulfillments
                    tracking_numbers = []
                    tracking_urls = []
                    tracking_status = []
                    
                    if hasattr(order, 'fulfillments'):
                        for fulfillment in order.fulfillments:
                            if fulfillment.tracking_number:
                                tracking_numbers.append(fulfillment.tracking_number)
                            if fulfillment.tracking_url:
                                tracking_urls.append(fulfillment.tracking_url)
                    
                    # Fetch tracking status if requested
                    if tracking_urls:
                        logger.info(f"Fetching tracking status for order {order.name}")
                        # Use ThreadPoolExecutor to fetch tracking statuses concurrently
                        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                            tracking_status = list(executor.map(fetch_tracking_status, tracking_urls))
                    
                    order_data = {
                        "order_number": order.name,
                        "created_at": order.created_at,
                        "status": order.financial_status,
                        "fulfillment_status": order.fulfillment_status,
                        "total_items": total_items,
                        "total_price": str(order.total_price),
                        "tracking_numbers": tracking_numbers,
                        "tracking_urls": tracking_urls,
                    }
                    
                    if tracking_status:
                        order_data["tracking_status"] = tracking_status
                    
                    matching_orders.append(order_data)
            
            matching_orders.sort(key=lambda x: x['created_at'], reverse=True)
            
            logger.info(f"Found {len(matching_orders)} orders for query: email={email}, phone={phone}")
            return Response({"orders": matching_orders})
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            error_details = format_exception()
            logger.error(f"Error fetching orders: {error_details}")
            
            if settings.DEBUG:
                return Response(error_details, status=500)
            return Response({"error": str(e)}, status=500) 