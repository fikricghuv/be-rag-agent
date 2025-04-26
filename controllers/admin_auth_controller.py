from fastapi import HTTPException
from models.generate_token_request_schema import AdminTokenRequest, AdminRefreshTokenRequest
from utils.admin_token_utils import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    store_refresh_token,
    validate_refresh_token
)

def generate_admin_token(request: AdminTokenRequest):
    access_token = create_access_token(request.admin_id)
    refresh_token = create_refresh_token(request.admin_id)

    store_refresh_token(refresh_token, request.admin_id)

    return {"token": access_token, "refresh_token": refresh_token}

def refresh_admin_token(request: AdminRefreshTokenRequest):
    admin_id = decode_refresh_token(request.refresh_token_admin)

    if not validate_refresh_token(request.refresh_token_admin, admin_id):
        raise HTTPException(status_code=401, detail="Refresh token not recognized")

    new_access_token = create_access_token(admin_id)
    return {"token": new_access_token}
