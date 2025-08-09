# app/api/endpoints/user_routes.py
import logging
from fastapi import APIRouter, Depends, Path, Body, status, HTTPException
from uuid import UUID
from middleware.token_dependency import verify_access_token
from schemas.user_schema import UserResponse, UserUpdate, UserCreate, UserListResponse
from services.user_service import UserService, get_user_service
from utils.exception_handler import handle_exceptions 
from middleware.auth_client_dependency import get_authenticated_client    
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])

@router.post("/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@handle_exceptions(tag="[USER]")
async def create_new_user(
    user_data: UserCreate = Body(...),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[USER] Creating new user with email: {user_data.email}")
    return user_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        client_id=client_id
    )

@router.get("/users/all", response_model=UserListResponse) 
@handle_exceptions(tag="[USER]")
async def get_user_profile(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
) -> Dict[str, Any]:
    logger.info(f"[USER] Fetching all user profile")
    users = user_service.get_all_user(client_id=client_id)
    
    total_users = len(users)

    return {
        "data": users,
        "total_users": total_users
    }

@router.get("/users/{user_id}", response_model=UserResponse)
@handle_exceptions(tag="[USER]")
async def get_user_profile(
    user_id: UUID = Path(..., description="ID unik pengguna"),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[USER] Fetching user profile for ID: {user_id}")
    user = user_service.get_user_by_id(str(user_id), client_id=client_id)
    if not user:
        logger.warning(f"[USER] User not found: {user_id}")
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
@handle_exceptions(tag="[USER]")
async def update_user_profile(
    user_id: UUID = Path(..., description="ID unik pengguna"),
    user_updates: UserUpdate = Body(...),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[USER] Updating profile for ID: {user_id}")
    updated_user = user_service.update_user_profile(str(user_id), user_updates.model_dump(exclude_unset=True), client_id=client_id)
    if not updated_user:
        logger.warning(f"[USER] Update failed: user {user_id} not found.")
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan atau tidak dapat diperbarui.")
    return updated_user

@router.delete("/users/{user_id}", status_code=204)
@handle_exceptions(tag="[USER]")
async def delete_user(
    user_id: UUID = Path(..., description="ID unik pengguna yang akan dihapus"),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[USER] Request to delete user with ID: {user_id}")
    user_service.delete_user(user_id=user_id, client_id=client_id)
    logger.info(f"[USER] User with ID {user_id} deleted successfully")
    return None 

