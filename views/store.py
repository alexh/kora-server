from fastapi import APIRouter, HTTPException, Depends, Query
from utils.auth import get_api_key
import shopify
from starlette.status import HTTP_404_NOT_FOUND
from django.core.cache import cache
import json
from datetime import datetime

router = APIRouter(prefix="/store", tags=["store"])

@router.get("/products")
async def get_products(api_key: str = Depends(get_api_key)):
    try:
        # Try to get from cache first
        cache_key = 'shopify_products'
        cached_products = cache.get(cache_key)
        
        if cached_products:
            return {"products": cached_products, "source": "cache"}
        
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
        
        return {"products": product_list, "source": "shopify"}
    except Exception as e:
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