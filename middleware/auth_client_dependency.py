from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from core.config_db import config_db
from database.models.client_model import Client
import logging

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_authenticated_client(
    request: Request,
    api_key: str = Depends(api_key_header),
    db: Session = Depends(config_db)
):
    """
    Dependency untuk validasi tenant berdasarkan subdomain + API Key
    """
    
    host = request.headers.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Host header missing")
    
    logger.info(f"[AUTH MIDDLEWARE] Authenticating client with host: {host} and API Key: {api_key}")

    # Ambil subdomain
    host_without_port = host.split(":")[0]
    parts = host_without_port.split(".")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid host format")

    subdomain = parts[0].lower()

    client = db.query(Client).filter(
        Client.subdomain == subdomain,
        Client.api_key == api_key
    ).first()

    if not client:
        logger.warning(f"Unauthorized access attempt. Subdomain: {subdomain}, API Key: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key or Subdomain"
        )

    if client.status != "active":
        logger.warning(f"Inactive client tried to access API: {client.name}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client is inactive"
        )
        
    request.state.client_id = client.id

    return client.id  
