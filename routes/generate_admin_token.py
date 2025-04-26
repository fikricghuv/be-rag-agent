from fastapi import APIRouter
from models.generate_token_request_schema import AdminTokenRequest, AdminRefreshTokenRequest
from controllers.admin_auth_controller import generate_admin_token, refresh_admin_token

router = APIRouter()

@router.post("/auth/generate-admin-token")
def generate_token(request: AdminTokenRequest):
    return generate_admin_token(request)

@router.post("/auth/refresh-admin-token")
def refresh_token_admin(request: AdminRefreshTokenRequest):
    return refresh_admin_token(request)
