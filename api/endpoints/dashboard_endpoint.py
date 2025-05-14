# app/api/endpoints/dashboard_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List, Dict, Any
# Mengimpor dependency service dan API Key
from services.chat_history_service import ChatHistoryService, get_chat_history_service
# Asumsi dependency api_key_auth diimpor dari services.verify_api_key_header
from services.verify_api_key_header import api_key_auth
# Tidak ada Pydantic model respons spesifik yang dibutuhkan untuk int atau List[Dict],
# jadi tidak perlu impor model respons di sini.

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["dashboard"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

@router.get("/stats/total-conversations", response_model=int, dependencies=[Depends(api_key_auth)])
async def get_total_conversations_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan total jumlah percakapan (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total conversations.")
        # Memanggil metode instance dari service
        total = chat_history_service.get_total_conversations()
        logger.info(f"Returning total conversations: {total}")
        return total
    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in get_total_conversations_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching total conversations."
        )
        
@router.get("/stats/total-users", response_model=int, dependencies=[Depends(api_key_auth)])
async def get_total_users_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan total jumlah user unik (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total unique users.")
        # Memanggil metode instance dari service
        total = chat_history_service.get_total_users()
        logger.info(f"Returning total unique users: {total}")
        return total
    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in get_total_users_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching total users."
        )

@router.get("/stats/categories-frequency", response_model=List[Dict[str, Any]], dependencies=[Depends(api_key_auth)])
async def get_categories_frequency_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan frekuensi kategori respons agent (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for categories frequency.")
        # Memanggil metode instance dari service
        categories = chat_history_service.get_categories_by_frequency()
        logger.info(f"Returning {len(categories)} categories frequency data.")
        return categories
    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in get_categories_frequency_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching categories frequency."
        )
