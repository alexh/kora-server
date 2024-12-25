from fastapi import FastAPI
import os
from dotenv import load_dotenv
import logging
from version import VERSION as version_number

# Load environment variables first
load_dotenv()

# Configure Django settings before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Shopify
from api.utils.shopify import init_shopify
init_shopify()

# Create FastAPI app
app = FastAPI(
    title="UMI API",
    description="API for Materials NYC operations",
    version=version_number
)

# Import and include routers
from views.health import router as health_router
from views.store import router as store_router
from views.feedback import router as feedback_router

app.include_router(health_router)
app.include_router(store_router)
app.include_router(feedback_router) 