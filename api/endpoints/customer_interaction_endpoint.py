import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query 
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from schemas.customer_feedback_response_schema import CustomerFeedbackResponse
from services.customer_interaction_service import CustomerInteractionService, get_customer_interaction_service 
from middleware.verify_api_key_header import api_key_auth
from schemas.customer_interaction_schema import PaginatedCustomerInteractionResponse, CustomerInteractionResponse
from fastapi.encoders import jsonable_encoder
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

router = APIRouter(
    tags=["customer-interactions"], 
)

@router.get("/interactions", response_model=PaginatedCustomerInteractionResponse)
async def get_all_customer_interactions_endpoint(
    customer_interaction: CustomerInteractionService = Depends(get_customer_interaction_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    access_token: str = Depends(verify_access_token) 
):
    try:
        result = customer_interaction.get_all_customer_interactions(offset, limit)

        return PaginatedCustomerInteractionResponse(
            total=result["total"],
            data=[
                CustomerInteractionResponse(**jsonable_encoder(row))
                for row in result["data"]
            ]
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_all_customer_interactions_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
