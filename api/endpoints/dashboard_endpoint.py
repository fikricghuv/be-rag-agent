import logging
from fastapi import APIRouter, Depends
from typing import List, Dict

from services.chat_history_service import ChatHistoryService, get_chat_history_service
from services.user_service import UserService, get_user_service
from schemas.customer_feedback_response_schema import CategoryFrequencyResponse
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/stats/total-conversations", response_model=int, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_total_conversations_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching total conversations")
    return chat_history_service.get_total_conversations()


@router.get("/stats/total-users", response_model=int, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_total_users_endpoint(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching total users")
    return user_service.get_total_users()


@router.get("/stats/total-tokens", response_model=float, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_total_tokens_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching total tokens used")
    return chat_history_service.get_total_tokens_used()


@router.get("/stats/categories-frequency", response_model=List[CategoryFrequencyResponse], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_categories_frequency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching categories frequency")
    return chat_history_service.get_categories_by_frequency()


@router.get("/stats/monthly-new-users", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_new_users_endpoint(
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching monthly new users")
    return user_service.get_monthly_user_additions()


@router.get("/stats/monthly-conversations", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_conversations_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching monthly conversations")
    return chat_history_service.get_monthly_conversations()


@router.get("/stats/daily-avg-latency", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_daily_average_latency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching daily average latency")
    return chat_history_service.get_daily_average_latency_seconds()


@router.get("/stats/monthly-avg-latency", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_average_latency_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching monthly average latency")
    return chat_history_service.get_monthly_average_latency_seconds()


@router.get("/stats/monthly-escalations", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_escalation_count_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching monthly escalations")
    return chat_history_service.get_escalation_by_month()


@router.get("/stats/monthly-tokens-usage", response_model=Dict[str, float], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_tokens_usage_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching monthly tokens usage")
    return chat_history_service.get_monthly_tokens_used()


@router.get("/stats/conversations/weekly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_weekly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching weekly conversations")
    return chat_history_service.get_conversations_by_week()


@router.get("/stats/conversations/monthly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching conversations by month")
    return chat_history_service.get_conversations_by_month()


@router.get("/stats/conversations/yearly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_yearly_conversations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching conversations by year")
    return chat_history_service.get_conversations_by_year()


@router.get("/stats/escalations/weekly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_weekly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching escalations by week")
    return chat_history_service.get_weekly_escalation_count()


@router.get("/stats/escalations/monthly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_monthly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching escalations by month")
    return chat_history_service.get_monthly_escalation_count()


@router.get("/stats/escalations/yearly", response_model=Dict[str, int], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[DASHBOARD]")
async def get_yearly_escalations_api(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[DASHBOARD] Fetching escalations by year")
    return chat_history_service.get_yearly_escalation_count()
