# app/api/endpoints/dashboard_routes.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List, Dict, Any
from services.chat_history_service import ChatHistoryService, get_chat_history_service
from services.verify_api_key_header import api_key_auth
from services.user_service import UserService, get_user_service

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
    user_service: UserService = Depends(get_user_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan total jumlah user unik (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total unique users.")
        # Memanggil metode instance dari service
        total = user_service.get_total_users()
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


@router.get("/stats/total-tokens", response_model=float, dependencies=[Depends(api_key_auth)])
async def get_total_tokens_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    Endpoint untuk mendapatkan total jumlah token yang digunakan di seluruh riwayat chat.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total tokens used.")
        total_tokens = chat_history_service.get_total_tokens_used()
        logger.info(f"Total tokens used: {total_tokens}")
        return total_tokens
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_total_tokens_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching total tokens."
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_total_tokens_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


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

@router.get("/stats/monthly-new-users", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_new_users_endpoint(
    user_service: UserService = Depends(get_user_service),
):
    """
    Endpoint untuk mendapatkan total penambahan user baru setiap bulan (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for monthly new users.")
        monthly_users_data = user_service.get_monthly_user_additions()
        logger.info(f"Returning monthly new users data: {monthly_users_data}")
        return monthly_users_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_new_users_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching monthly new users."
        )
        
@router.get("/stats/monthly-conversations", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_conversations_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
):
    """
    Endpoint untuk mendapatkan total percakapan bulanan (untuk dashboard).
    Percakapan dihitung berdasarkan room_conversation_id unik.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for monthly conversations.")
        monthly_conversations_data = chat_history_service.get_monthly_conversations()
        logger.info(f"Returning monthly conversations data: {monthly_conversations_data}")
        return monthly_conversations_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_conversations_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching monthly conversations."
        )
        
@router.get("/stats/daily-avg-latency", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
async def get_daily_average_latency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
):
    """
    Endpoint untuk mendapatkan latensi rata-rata harian dalam milidetik.
    Membutuhkan API Key yang valid.
    """
    try:
        logger.info("Received request for daily average latency.")
        daily_latency_data = chat_history_service.get_daily_average_latency_seconds()
        logger.info(f"Returning daily average latency data: {daily_latency_data}")
        return daily_latency_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_daily_average_latency_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching daily average latency."
        )

@router.get("/stats/monthly-avg-latency", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
async def get_monthly_average_latency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
):
    """
    Endpoint untuk mendapatkan latensi rata-rata bulanan dalam milidetik.
    Membutuhkan API Key yang valid.
    """
    try:
        logger.info("Received request for monthly average latency.")
        monthly_latency_data = chat_history_service.get_monthly_average_latency_seconds()
        logger.info(f"Returning monthly average latency data: {monthly_latency_data}")
        return monthly_latency_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_average_latency_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching monthly average latency."
        )