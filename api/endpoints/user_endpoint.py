# app/api/endpoints/user_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path
from middleware.verify_api_key_header import api_key_auth
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from schemas.user_schema import UserResponse, UserUpdate, UserCreate
from services.user_service import UserService, get_user_service
from fastapi import Body
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["user"], 
)

@router.post("/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_data: UserCreate = Body(...),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Membuat user baru.
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
        raise e # Lempar kembali HTTPException yang sudah dibuat di service
    except Exception as e:
        logger.error(f"Unexpected error creating user {user_data.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan tak terduga: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(api_key_auth)])
async def get_user_profile(
    user_id: UUID = Path(..., description="ID unik pengguna"), # Menggunakan UUID untuk validasi Path
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil profil pengguna berdasarkan ID.
    """
    try:
        logger.info(f"Request to get user profile for ID: {user_id}")
        user = user_service.get_user_by_id(str(user_id)) # UserService mengharapkan string UUID
        if not user:
            logger.warning(f"User with ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pengguna tidak ditemukan."
            )
        logger.info(f"Successfully retrieved user profile for ID: {user_id}")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan saat mengambil data pengguna dari database."
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(api_key_auth)])
async def update_user_profile(
    user_id: UUID = Path(..., description="ID unik pengguna"),
    user_updates: UserUpdate = Body(...),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Memperbarui informasi profil pengguna berdasarkan ID.
    """
    try:
        logger.info(f"Request to update user profile for ID: {user_id} with data: {user_updates.dict()}")
        # Gunakan .dict(exclude_unset=True) untuk hanya mengirim field yang disediakan klien
        updated_user = user_service.update_user_profile(str(user_id), user_updates.model_dump(exclude_unset=True))
        if not updated_user:
            logger.warning(f"User with ID {user_id} not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pengguna tidak ditemukan atau tidak dapat diperbarui."
            )
        logger.info(f"Successfully updated user profile for ID: {user_id}")
        return updated_user
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan saat memperbarui data pengguna di database."
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )
