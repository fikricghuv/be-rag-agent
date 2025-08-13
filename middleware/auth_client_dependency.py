from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.config_db import config_db
from database.models.client_model import Client
from jose import jwt, JWTError
from core.settings import SECRET_KEY_ADMIN, ALGORITHM
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
security = HTTPBearer(auto_error=False)  # supaya bisa optional

def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str | None:
    if credentials:
        return credentials.credentials
    return None

def get_authenticated_client(
    request: Request,
    api_key: str | None = Depends(api_key_header),
    access_token: str | None = Depends(get_access_token),
    db: Session = Depends(config_db),
):
    """
    Validasi client:
    - Jika ada access_token (bearer): validasi JWT dan ambil client_id
    - Jika tidak ada access_token, pakai api_key + subdomain
    """

    host = request.headers.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Host header missing")

    logger.info(f"[AUTH MIDDLEWARE] Authenticating client with host: {host}, API Key: {api_key}, Access Token present: {access_token}")

    if access_token:
        logger.info(f"[AUTH MIDDLEWARE] Validating access token")
        try:
            payload = jwt.decode(access_token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id"
                )

            result = db.execute(
                text("""
                    SELECT client_id
                    FROM ai.ms_admin_users
                    WHERE id = :user_id
                """),
                {"user_id": user_id}
            ).fetchone()

            if not result or not result.client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User identity not found or client_id missing"
                )

            client = db.query(Client).filter(Client.id == result.client_id).first()
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Client not found"
                )
            if client.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Client is inactive"
                )

            request.state.client_id = client.id
            return client.id

        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    # Kalau gak ada access_token, cek api_key + subdomain
    host_without_port = host.split(":")[0]
    parts = host_without_port.split(".")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid host format")

    subdomain = parts[0].lower()

    if api_key:
        logger.info(f"[AUTH MIDDLEWARE] Validating API Key for subdomain: {subdomain}")
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

    # Kalau gak ada api_key dan access_token
    raise HTTPException(status_code=401, detail="Missing API Key or Access Token")
