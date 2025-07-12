# app/api/endpoints/customer_feedback_endpoint.py
import logging
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from schemas.customer_feedback_response_schema import CustomerFeedbackResponse
from services.customer_feedback_service import CustomerFeedbackService, get_customer_feedback_service
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token
from middleware.log_user_activity import log_user_activity
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["customer-feedback"])

@router.get("/feedbacks", response_model=List[CustomerFeedbackResponse], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[FEEDBACK]")
async def get_feedbacks_endpoint(
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service),
    offset: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return per page", le=200),
    search: Optional[str] = Query(None, description="Search keyword on feedback"),
    access_token: str = Depends(verify_access_token)
):
    logger.info(f"[FEEDBACK] Request: offset={offset}, limit={limit}, search='{search}'")
    feedbacks = customer_feedback_service.fetch_all_feedbacks(offset=offset, limit=limit, search=search)
    logger.info(f"[FEEDBACK] Returned {len(feedbacks)} feedback entries.")
    return feedbacks

@router.get("/feedbacks/total", response_model=int, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[FEEDBACK_TOTAL]")
async def get_total_feedbacks_endpoint(
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[FEEDBACK_TOTAL] Request received.")
    total_feedbacks = customer_feedback_service.count_total_feedbacks()
    logger.info(f"[FEEDBACK_TOTAL] Returning count: {total_feedbacks}")
    return total_feedbacks
