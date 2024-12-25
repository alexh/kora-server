from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os

API_KEY_NAME = "X-API-Key"
ADMIN_KEY_NAME = "X-Admin-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
admin_key_header = APIKeyHeader(name=ADMIN_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == os.getenv("API_KEY"):
        return api_key_header
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
    )

async def get_admin_key(admin_key_header: str = Security(admin_key_header)):
    if admin_key_header == os.getenv("ADMIN_API_KEY"):
        return admin_key_header
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate admin key"
    ) 