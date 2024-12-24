from fastapi import APIRouter
from version import VERSION as version_number
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def root():
    return {"message": f"Welcome to UMI API v{version_number}"}

@router.get("/health-check")
async def health_check():
    logger.info("Health check called")
    try:
        # Wrap DB operations in sync_to_async
        @sync_to_async
        def check_db():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        
        await check_db()
        logger.info("Health check passed")
        return {"message": "Server is running", "status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"message": "Server is running", "status": "unhealthy", "error": str(e)}

@router.get("/version")
async def version():
    return {"version": version_number} 