import logging
from fastapi import APIRouter, Depends, Query
from typing import List
from fastapi.encoders import jsonable_encoder
from schemas.customer_interaction_schema import PaginatedCustomerInteractionResponse, CustomerInteractionResponse
from services.customer_interaction_service import CustomerInteractionService, get_customer_interaction_service
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["customer-interactions"])

@router.get("/interactions", response_model=PaginatedCustomerInteractionResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[INTERACTION]")
async def get_all_customer_interactions_endpoint(
    customer_interaction: CustomerInteractionService = Depends(get_customer_interaction_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    access_token: str = Depends(verify_access_token)
):
    """
    Endpoint untuk mendapatkan semua interaksi customer dengan pagination.
    Membutuhkan access token dan API key yang valid.
    """
    logger.info(f"[INTERACTION] Fetching interactions offset={offset}, limit={limit}")
    result = customer_interaction.get_all_customer_interactions(offset, limit)

    logger.info(f"[INTERACTION] Fetched total={result['total']}")
    return PaginatedCustomerInteractionResponse(
        total=result["total"],
        data=[
            CustomerInteractionResponse(**jsonable_encoder(row))
            for row in result["data"]
        ]
    )
