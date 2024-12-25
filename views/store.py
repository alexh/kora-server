from fastapi import APIRouter, HTTPException, Depends, Query
from api.utils import send_discord_webhook
from utils.auth import get_api_key
import shopify
from starlette.status import HTTP_404_NOT_FOUND
from django.core.cache import cache
import json
from datetime import datetime, timedelta
import logging

# Configure logger at the top of the file
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/store", tags=["store"])

@router.get("/products")
async def get_products(api_key: str = Depends(get_api_key)):
    try:
        logger.info("Starting product fetch request")
        
        # Try to get from cache first
        cache_key = 'shopify_products'
        cached_products = cache.get(cache_key)
        
        if cached_products:
            logger.info("Returning products from cache")
            return {"products": cached_products, "source": "cache"}
        
        logger.info("Cache miss - fetching products from Shopify")
        products = shopify.Product.find(status='active')
        product_list = []
        
        total_products = len(products)
        total_variants = 0
        out_of_stock_products = 0
        low_stock_products = []

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
            
            product_has_stock = any(v["in_stock"] for v in variants)
            if not product_has_stock:
                out_of_stock_products += 1
            elif any(0 < v["inventory_quantity"] <= 5 for v in variants):
                low_stock_products.append(product.title)
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
                "has_stock": any(v["in_stock"] for v in variants),
                "url": f"https://materials.nyc/products/{product.handle}"
            })
        
        logger.info(
            f"Product stats: {total_products} products, {total_variants} variants, "
            f"{out_of_stock_products} out of stock, {len(low_stock_products)} low stock"
        )
        
        # Store in cache
        cache.set(cache_key, product_list, timeout=300)
        logger.info("Products cached successfully")

        # Send Discord webhook
        logger.info("Sending Discord webhook notification")
        send_discord_webhook(
            title="🏪 Product Inventory Update",
            description="Latest product catalog refresh completed",
            fields=[
                {
                    "name": "📊 Total Products",
                    "value": str(total_products),
                    "inline": True
                },
                {
                    "name": "🔄 Total Variants",
                    "value": str(total_variants),
                    "inline": True
                },
                {
                    "name": "⚠️ Out of Stock",
                    "value": f"{out_of_stock_products} products",
                    "inline": True
                },
                {
                    "name": "⚡ Cache Status",
                    "value": "✅ Updated",
                    "inline": True
                },
                {
                    "name": "⏱️ Cache Expiry",
                    "value": "5 minutes",
                    "inline": True
                }
            ] + ([{
                "name": "📉 Low Stock Products",
                "value": "\n".join(f"• {product}" for product in low_stock_products[:5]),
                "inline": False
            }] if low_stock_products else []),
            color="ff5f05",  # Orange color
            timestamp=True
        )
        logger.info("Discord webhook sent successfully")
        
        return {"products": product_list, "source": "shopify"}
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}", exc_info=True)
        # Send error notification
        send_discord_webhook(
            title="❌ Product Fetch Error",
            description="Failed to fetch products from Shopify",
            fields=[{
                "name": "Error Details",
                "value": f"```{str(e)}```",
                "inline": False
            }]
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_number}")
async def lookup_order(
    order_number: str,
    email: str | None = Query(None, description="Customer email used for the order"),
    phone: str | None = Query(None, description="Customer phone number used for the order"),
    api_key: str = Depends(get_api_key)
):
    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="Either email or phone number must be provided"
        )

    try:
        # Remove '#' from order number if present
        order_number = order_number.replace('#', '')
        
        # Search for orders
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
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No order found matching this order number and contact information"
            )
        
        # Format line items (without personal info)
        line_items = []
        for item in matching_order.line_items:
            line_items.append({
                "title": item.title,
                "quantity": item.quantity,
                "variant_title": item.variant_title
            })
        
        return {
            "order_number": matching_order.name,
            "created_at": matching_order.created_at,
            "status": matching_order.financial_status,
            "fulfillment_status": matching_order.fulfillment_status,
            "line_items": line_items
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders")
async def get_customer_orders(
    email: str | None = Query(None, description="Customer email"),
    phone: str | None = Query(None, description="Customer phone number"),
    api_key: str = Depends(get_api_key)
):
    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="Either email or phone number must be provided"
        )
    
    try:
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
        
        return {"orders": matching_orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))