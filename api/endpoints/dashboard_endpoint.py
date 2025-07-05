# app/api/endpoints/dashboard_routes.py
import logging 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any
from services.chat_history_service import ChatHistoryService, get_chat_history_service
from middleware.verify_api_key_header import api_key_auth
from services.user_service import UserService, get_user_service
from schemas.customer_feedback_response_schema import CategoryFrequencyResponse
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["dashboard"], 
)

@router.get("/stats/total-conversations", response_model=int, dependencies=[Depends(api_key_auth)])
async def get_total_conversations_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan total jumlah percakapan (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total conversations.")
        
        total = chat_history_service.get_total_conversations()
        logger.info(f"Returning total conversations: {total}")
        return total
    
    except SQLAlchemyError as e:
        
        logger.error(f"Database error in get_total_conversations_endpoint: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching total conversations."
        )
        
@router.get("/stats/total-users", response_model=int, dependencies=[Depends(api_key_auth)])
async def get_total_users_endpoint(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan total jumlah user unik (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total unique users.")
        
        total = user_service.get_total_users()
        logger.info(f"Returning total unique users: {total}")
        return total
    
    except SQLAlchemyError as e:
        
        logger.error(f"Database error in get_total_users_endpoint: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching total users."
        )

@router.get("/stats/total-tokens", response_model=float, dependencies=[Depends(api_key_auth)])
async def get_total_tokens_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
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


@router.get("/stats/categories-frequency", response_model=List[CategoryFrequencyResponse], dependencies=[Depends(api_key_auth)])
async def get_categories_frequency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan frekuensi kategori respons agent (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for categories frequency.")
        
        categories = chat_history_service.get_categories_by_frequency()
        logger.info(f"Returning {len(categories)} categories frequency data.")
        return categories
    
    except SQLAlchemyError as e:
        
        logger.error(f"Database error in get_categories_frequency_endpoint: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching categories frequency."
        )

@router.get("/stats/monthly-new-users", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_new_users_endpoint(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token) 
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
    access_token: str = Depends(verify_access_token) 
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
    access_token: str = Depends(verify_access_token) 
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
    access_token: str = Depends(verify_access_token) 
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

@router.get("/stats/monthly-escalations", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_escalation_count_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan total eskalasi bulanan.
    Eskalasi diidentifikasi jika agent memanggil tool untuk menyimpan data feedback pelanggan.
    Mengembalikan data untuk setiap bulan dari Januari hingga bulan saat ini, dengan 0 jika tidak ada data.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for monthly escalation count.")
        monthly_escalation_data = chat_history_service.get_escalation_by_month()
        logger.info(f"Returning monthly escalation count data: {monthly_escalation_data}")
        return monthly_escalation_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_escalation_count_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching monthly escalation count."
        )
        
@router.get("/stats/monthly-tokens-usage", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
async def get_monthly_tokens_usage_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan total penggunaan token per bulan selama tahun berjalan (untuk dashboard).
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for monthly tokens usage.")
        monthly_tokens_data = chat_history_service.get_monthly_tokens_used()
        logger.info(f"Returning monthly tokens usage data: {monthly_tokens_data}")
        return monthly_tokens_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_tokens_usage_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching monthly tokens usage."
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_monthly_tokens_usage_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
    
@router.get("/stats/conversations/weekly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_weekly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total percakapan unik untuk 12 minggu terakhir.
    Mengembalikan dictionary dengan format {'YYYY-WW': total_conversations}.
    """
    try:
        logger.info("Received request for weekly total conversations.")
        weekly_data = chat_history_service.get_conversations_by_week()
        logger.info(f"Returning weekly conversation data: {weekly_data}")
        return weekly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_weekly_conversations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch weekly conversation statistics."
        )

@router.get("/stats/conversations/monthly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total percakapan unik untuk 12 bulan terakhir.
    Mengembalikan dictionary dengan format {'YYYY-MM': total_conversations}.
    """
    try:
        logger.info("Received request for monthly total conversations.")
        monthly_data = chat_history_service.get_conversations_by_month()
        logger.info(f"Returning monthly conversation data: {monthly_data}")
        return monthly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_conversations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch monthly conversation statistics."
        )

@router.get("/stats/conversations/yearly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_yearly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total percakapan unik untuk 6 tahun terakhir.
    Mengembalikan dictionary dengan format {'YYYY': total_conversations}.
    """
    try:
        logger.info("Received request for yearly total conversations.")
        yearly_data = chat_history_service.get_conversations_by_year()
        logger.info(f"Returning yearly conversation data: {yearly_data}")
        return yearly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_yearly_conversations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch yearly conversation statistics."
        )

@router.get("/stats/escalations/weekly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_weekly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total eskalasi unik untuk 12 minggu terakhir.
    Eskalasi diidentifikasi jika agent memanggil tool untuk menyimpan data feedback pelanggan.
    Mengembalikan dictionary dengan format {'YYYY-WW': total_escalations}.
    """
    try:
        logger.info("Received request for weekly escalations.")
        weekly_data = chat_history_service.get_weekly_escalation_count()
        logger.info(f"Returning weekly escalation data: {weekly_data}")
        return weekly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_weekly_escalations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch weekly escalation statistics."
        )

@router.get("/stats/escalations/monthly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_monthly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total eskalasi unik untuk 12 bulan terakhir.
    Eskalasi diidentifikasi jika agent memanggil tool untuk menyimpan data feedback pelanggan.
    Mengembalikan dictionary dengan format {'YYYY-MM': total_escalations}.
    """
    try:
        logger.info("Received request for monthly escalations.")
        monthly_data = chat_history_service.get_monthly_escalation_count()
        logger.info(f"Returning monthly escalation data: {monthly_data}")
        return monthly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_escalations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch monthly escalation statistics."
        )

@router.get("/stats/escalations/yearly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
async def get_yearly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Mengambil total eskalasi unik untuk 6 tahun terakhir.
    Eskalasi diidentifikasi jika agent memanggil tool untuk menyimpan data feedback pelanggan.
    Mengembalikan dictionary dengan format {'YYYY': total_escalations}.
    """
    try:
        logger.info("Received request for yearly escalations.")
        yearly_data = chat_history_service.get_yearly_escalation_count()
        logger.info(f"Returning yearly escalation data: {yearly_data}")
        return yearly_data
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_yearly_escalations_api: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch yearly escalation statistics."
        )