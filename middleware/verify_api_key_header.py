# # middleware/api_key_auth.py
# from fastapi.security import APIKeyHeader
# from fastapi import HTTPException, Depends, status
# import logging
# from core.settings import VALID_API_KEYS

# logger = logging.getLogger(__name__)
# api_key_header = APIKeyHeader(name="X-API-Key")

# def api_key_auth(api_key: str = Depends(api_key_header)):
#     """
#     Dependency untuk memvalidasi API Key dari header 'X-API-Key'.
#     """
#     if api_key not in VALID_API_KEYS:
#         logger.warning(f"Unauthorized API key attempt: {api_key}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid API Key",
#         )
#     return api_key

from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.models.client_model import Client
from core.config_db import config_db
import logging

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key")

async def api_key_auth(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(config_db)
):
    """
    Dependency untuk memvalidasi API Key dari database (tabel clients).
    """
    client = db.query(Client).filter(Client.api_key == api_key).first()
    
    if not client:
        logger.warning(f"Unauthorized API key attempt: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    if client.status != "active":
        logger.warning(f"Inactive client tried to access API: {client.name}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client is inactive",
        )

    return client.id  # Bisa return client.id agar service tahu client mana yang akses
