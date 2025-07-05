# app/api/endpoints/customer_feedback_endpoint.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query 
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from schemas.customer_feedback_response_schema import CustomerFeedbackResponse
from services.customer_feedback_service import CustomerFeedbackService, get_customer_feedback_service 
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

router = APIRouter(
    tags=["customer-feedback"], 
)

@router.get("/feedbacks", response_model=List[CustomerFeedbackResponse], dependencies=[Depends(api_key_auth)])
async def get_feedbacks_endpoint(
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service),
    offset: int = Query(0, description="Number of items to skip"), 
    limit: int = Query(100, description="Number of items to return per page", le=200),
    access_token: str = Depends(verify_access_token)  
):
    """
    Endpoint untuk mendapatkan semua feedback customer dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    try:
        logger.info(f"Received request for customer feedbacks with offset={offset}, limit={limit}.")
        feedbacks = customer_feedback_service.fetch_all_feedbacks(offset=offset, limit=limit)

        logger.info(f"Returning {len(feedbacks)} feedback entries.")
        return feedbacks

    except SQLAlchemyError as e:
        logger.error(f"Database error in get_feedbacks_endpoint: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer feedbacks due to an internal server issue."
        )

@router.get("/feedbacks/total", response_model=int, dependencies=[Depends(api_key_auth)])
async def get_total_feedbacks_endpoint(
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service),
    access_token: str = Depends(verify_access_token)
):
    """
    Endpoint untuk mendapatkan total jumlah feedback customer.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request for total customer feedbacks.")
        total_feedbacks = customer_feedback_service.count_total_feedbacks()
        logger.info(f"Returning total feedback count: {total_feedbacks}.")
        return total_feedbacks
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_total_feedbacks_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not count total customer feedbacks due to a server error."
        )