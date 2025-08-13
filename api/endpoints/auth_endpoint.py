from fastapi import APIRouter, Depends, Body, status
from datetime import datetime
from jose import jwt
from core.settings import SECRET_KEY_ADMIN, ALGORITHM
from services.auth_service import AuthService, get_auth_service
from services.user_service import UserService, get_user_service
from middleware.auth_client_dependency import get_authenticated_client
from middleware.get_current_user import get_current_user
from schemas.user_schema import UserCreate, UserResponse
from schemas.user_id_schema import GenerateUserIdRequest, UserIdResponse
from schemas.token_schema import GenerateTokenRequest, TokenResponse, RefreshTokenRequest
from schemas.login_schema import LoginRequest
from database.models.user_model import User
from utils.exception_handler import handle_exceptions
import logging
from uuid import UUID
from middleware.token_dependency import verify_access_token_and_get_client_id


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

@router.post("/auth/generate_user_id", response_model=UserIdResponse, status_code=status.HTTP_201_CREATED)
@handle_exceptions(tag="[AUTH]")
async def generate_user_id_endpoint(
    request: GenerateUserIdRequest = Body(...),
    client_id: UUID = Depends(get_authenticated_client),
    auth_service: AuthService = Depends(get_auth_service),
):
    logger.info(f"[AUTH] Generating user_id with role={request.role}")
    return auth_service.generate_user_id(role=request.role, client_id=client_id)

@router.post("/auth/generate_token", response_model=TokenResponse)
@handle_exceptions(tag="[AUTH]")
async def generate_token_endpoint(
    request: GenerateTokenRequest = Body(...),
    client_id: UUID = Depends(get_authenticated_client),
    auth_service: AuthService = Depends(get_auth_service)
):
    logger.info(f"[AUTH] Generating access + refresh token for user_id={request.user_id}")
    access_data = auth_service.generate_access_token(user_id=request.user_id)
    refresh_token = auth_service.generate_refresh_token(user_id=request.user_id)

    expires_in = access_data["expires_at"] - int(datetime.utcnow().timestamp())

    return TokenResponse(
        access_token=access_data["access_token"],
        refresh_token=refresh_token,
        expires_in=expires_in
    )

@router.post("/auth/refresh", response_model=TokenResponse)
@handle_exceptions(tag="[AUTH]")
async def refresh_token_endpoint(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[AUTH] Refreshing token")
    payload = jwt.decode(request.refresh_token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("Invalid refresh token")

    new_access_data = auth_service.generate_access_token(user_id=user_id)
    new_refresh_token = auth_service.generate_refresh_token(user_id=user_id)

    return TokenResponse(
        access_token=new_access_data["access_token"],
        refresh_token=new_refresh_token,
        expires_in=new_access_data["expires_at"]
    )

@router.post("/auth/login", response_model=TokenResponse)
@handle_exceptions(tag="[AUTH]")
async def login_endpoint(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    # client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[AUTH] Login attempt for email={request.email}")
    tokens = auth_service.login_user(email=request.email, password=request.password)

    expires_in = tokens["expires_at"] - int(datetime.utcnow().timestamp())

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=expires_in
    )

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@handle_exceptions(tag="[AUTH]")
def create_new_user(
    user_data: UserCreate = Body(...),
    user_service: UserService = Depends(get_user_service),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[AUTH] Registering new user with email={user_data.email}, role={user_data.role}")
    return user_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        client_id=client_id
    )

@router.get("/auth/me", response_model=UserResponse)
@handle_exceptions(tag="[AUTH]")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[AUTH] Fetching profile for user_id={current_user.id}, email={current_user.email}")
    return current_user
