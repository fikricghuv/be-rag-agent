# app/api/endpoints/room_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query # Import status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List
# Mengimpor dependency service dan API Key
from services.room_service import RoomService, get_room_service # Menggunakan service class dan dependency
# Asumsi dependency api_key_auth diimpor dari services.verify_api_key_header
from services.verify_api_key_header import api_key_auth
# Mengimpor Pydantic model respons
from schemas.room_conversation_schema import RoomConversationResponse # Menggunakan schema yang ada

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["rooms"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

# Mengubah dari POST menjadi GET
# Mengubah path dari /get-all-room menjadi /rooms (lebih RESTful)
# Menambahkan API Key Authentication
# Menambahkan parameter pagination
@router.get("/rooms/get-all-rooms", response_model=List[RoomConversationResponse], dependencies=[Depends(api_key_auth)])
async def get_all_rooms_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    room_service: RoomService = Depends(get_room_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
    # --- Parameter Pagination ---
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200), # Default 100, maks 200
):
    """
    Endpoint untuk mendapatkan semua room conversations dengan pagination (untuk admin view).
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    try:
        logger.info(f"Received request for all rooms with offset={offset}, limit={limit}.")
        # Memanggil metode instance dari service, meneruskan parameter pagination
        rooms = room_service.get_all_rooms(offset=offset, limit=limit)

        # Pydantic dengan orm_mode=True akan otomatis mengonversi List[RoomConversation] menjadi List[RoomConversationResponse]
        logger.info(f"Returning {len(rooms)} room entries.")
        return rooms

    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in get_all_rooms_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching rooms."
        )
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in get_all_rooms_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/rooms/active-rooms", response_model=List[RoomConversationResponse], dependencies=[Depends(api_key_auth)])
async def get_active_rooms_endpoint(
    room_service: RoomService = Depends(get_room_service),
    offset: int = Query(0, description="Number of active items to skip"),
    limit: int = Query(100, description="Number of active items to return per page", le=200),
):
    """
    Endpoint untuk mendapatkan room conversations yang aktif dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item aktif yang akan dilewati.
        limit: Jumlah item aktif per halaman.
    """
    try:
        logger.info(f"Received request for active rooms with offset={offset}, limit={limit}.")
        active_rooms = room_service.get_active_rooms(offset=offset, limit=limit)
        logger.info(f"Returning {len(active_rooms)} active room entries.")
        return active_rooms
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_active_rooms_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching active rooms."
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_active_rooms_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
