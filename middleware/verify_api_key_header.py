# middleware/api_key_auth.py
from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Depends, status
import logging
from core.settings import VALID_API_KEYS

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key")

def api_key_auth(api_key: str = Depends(api_key_header)):
    """
    Dependency untuk memvalidasi API Key dari header 'X-API-Key'.
    """
    if api_key not in VALID_API_KEYS:
        logger.warning(f"Unauthorized API key attempt: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
