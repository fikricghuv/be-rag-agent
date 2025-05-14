# app/routes/chat_history_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path # Import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List
# Mengimpor dependency service dan API Key
from services.chat_history_service import ChatHistoryService, get_chat_history_service # Menggunakan ChatHistoryService dan dependencynya
from services.verify_api_key_header import api_key_auth # Pastikan path import ini benar
# Mengimpor Pydantic model respons
from schemas.chat_history_schema import ChatHistoryResponse, UserHistoryResponse
from uuid import UUID # Import UUID type

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["history"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

# Endpoint untuk mengambil semua chat history
# Mengubah path dari /history/history-chat menjadi /history/all
# Menerapkan API Key Authentication
@router.get("/history/all", response_model=List[ChatHistoryResponse], dependencies=[Depends(api_key_auth)])
async def read_all_chat_history_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
    # --- Parameter Pagination ---
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200), # Default 100, maks 200
):
    """
    Endpoint untuk mendapatkan semua riwayat chat dengan pagination (untuk monitoring).
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    try:
        logger.info(f"Received request for all chat history with offset={offset}, limit={limit}.")
        # Memanggil metode instance dari service, meneruskan parameter pagination
        # CATATAN: Pastikan metode get_all_chat_history di ChatHistoryService
        # menerima parameter offset dan limit dan menggunakannya dalam query SQLAlchemy
        chat_history = chat_history_service.get_all_chat_history(offset=offset, limit=limit)

        # Pydantic dengan orm_mode=True akan otomatis mengonversi List[Chat] menjadi List[ChatHistoryResponse]
        logger.info(f"Returning {len(chat_history)} chat entries.")
        return chat_history

    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in read_all_chat_history_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching chat history."
        )
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in read_all_chat_history_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/history/{user_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
async def get_user_history_endpoint( # Mengubah nama fungsi untuk konsistensi
    # Menerima room_id sebagai UUID dari path
    user_id: UUID = Path(..., description="UUID of the user"), # Menggunakan UUID dan Path
    # Menggunakan dependency untuk mendapatkan instance service
    # Menggunakan ChatHistoryService yang sudah ada
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
    # --- Parameter Pagination ---
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200), # Default 100, maks 200
):
    """
    Endpoint untuk mendapatkan riwayat chat untuk user spesifik dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        room_id: UUID dari user.
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    logger.info(f"Received request for history for user {user_id} with offset={offset}, limit={limit}.")
    try:
        history = chat_history_service.get_user_chat_history_by_user_id(user_id, offset=offset, limit=limit)

        # Mengembalikan respons sesuai UserHistoryResponse schema
        logger.info(f"Returning {len(history)} history entries for room {user_id}.")

        return UserHistoryResponse(
            success=True,
            room_id=user_id,
            user_id=user_id,
            history = [ChatHistoryResponse.model_validate(chat) for chat in history]

        )


    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching history for room {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching room history."
        )
    # Menangkap HTTPException yang mungkin dilempar oleh service (misalnya 404 jika user tidak ditemukan,
    # meskipun service get_user_chat_history mungkin mengembalikan list kosong)
    except HTTPException as e:
         logger.warning(f"HTTPException raised fetching history for room {user_id}: {e.detail}", exc_info=True)
         raise e # Re-raise HTTPException
    # Menangkap error tak terduga lainnya
    except Exception as e:
        logger.error(f"Unexpected error fetching history for room {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/history/room/{room_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
async def get_user_history_endpoint( # Mengubah nama fungsi untuk konsistensi
    # Menerima room_id sebagai UUID dari path
    room_id: UUID = Path(..., description="UUID of the user"), # Menggunakan UUID dan Path
    # Menggunakan dependency untuk mendapatkan instance service
    # Menggunakan ChatHistoryService yang sudah ada
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
    # --- Parameter Pagination ---
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200), # Default 100, maks 200
):
    """
    Endpoint untuk mendapatkan riwayat chat untuk user spesifik dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        room_id: UUID dari user.
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    logger.info(f"Received request for history for user {room_id} with offset={offset}, limit={limit}.")
    try:
        result = chat_history_service.get_user_chat_history_by_room_id(room_id, offset=offset, limit=limit)

        if not result:
            raise HTTPException(status_code=404, detail="No chat history or user found for this room.")

        user_id = result["user_id"]
        history = result["history"]
        print(f"/n-----------ini user id {user_id}")
        logger.info(f"Returning {len(history)} history entries for room {room_id}.")

        return UserHistoryResponse(
            success=True,
            room_id=room_id,
            user_id=user_id,
            history=[ChatHistoryResponse.model_validate(chat) for chat in history]
        )


    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching history for room {room_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching room history."
        )
    # Menangkap HTTPException yang mungkin dilempar oleh service (misalnya 404 jika user tidak ditemukan,
    # meskipun service get_user_chat_history mungkin mengembalikan list kosong)
    except HTTPException as e:
         logger.warning(f"HTTPException raised fetching history for room {room_id}: {e.detail}", exc_info=True)
         raise e # Re-raise HTTPException
    # Menangkap error tak terduga lainnya
    except Exception as e:
        logger.error(f"Unexpected error fetching history for room {room_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

