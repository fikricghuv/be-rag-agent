# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, Body, Depends, status, HTTPException
from services.auth_service import AuthService, get_auth_service
from middleware.verify_api_key_header import api_key_auth
from schemas.user_id_schema import UserIdResponse, GenerateUserIdRequest
from pydantic import BaseModel
from schemas.token_schema import GenerateTokenRequest, TokenResponse, RefreshTokenRequest
from schemas.login_schema import LoginRequest
from schemas.user_schema import UserResponse, UserCreate
from services.user_service import UserService, get_user_service
import logging
from jose import jwt 
from core.settings import SECRET_KEY_REFRESH_ADMIN, ALGORITHM
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["auth"], 
)

@router.post("/auth/generate_user_id", response_model=UserIdResponse, 
             status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(api_key_auth)])
async def generate_user_id_endpoint(
    request: GenerateUserIdRequest = Body(..., description="Request body with the desired role"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint untuk menghasilkan user_id berdasarkan peran yang diterima di request body.
    Mengembalikan detail user_id yang baru dibuat.
    """
    
    user_data = auth_service.generate_user_id(role=request.role)
    
    return user_data

@router.post("/auth/generate_token", response_model=TokenResponse,
             dependencies=[Depends(api_key_auth)])
async def generate_token_endpoint(
    request: GenerateTokenRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint untuk menghasilkan JWT access token berdasarkan user_id.
    """
    
    user_id = request.user_id
    access_token = auth_service.generate_access_token(user_id=user_id)
    refresh_token = auth_service.generate_refresh_token(user_id=user_id)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY_REFRESH_ADMIN, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = auth_service.generate_access_token(user_id=user_id)
        new_refresh_token = auth_service.generate_refresh_token(user_id=user_id)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token  
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/auth/login", response_model=TokenResponse)
async def login_endpoint(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = auth_service.login_user(email=request.email, password=request.password)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"]
    )

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_data: UserCreate = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Membuat user baru. Hanya bisa diakses jika user sudah login (punya access token).
    """
    logger.info(f"Request to create new user with email: {user_data.email}")
    try:
        new_user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        logger.info(f"User {new_user.email} created successfully.")
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error creating user {user_data.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan tak terduga: {str(e)}"
        )