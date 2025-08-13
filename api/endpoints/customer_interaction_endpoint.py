import logging
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from schemas.customer_interaction_schema import PaginatedCustomerInteractionResponse, CustomerInteractionResponse
from services.customer_interaction_service import CustomerInteractionService, get_customer_interaction_service
from middleware.token_dependency import verify_access_token_and_get_client_id
from utils.exception_handler import handle_exceptions
from uuid import UUID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["customer-interactions"])

@router.get("/interactions", response_model=PaginatedCustomerInteractionResponse)
@handle_exceptions(tag="[INTERACTION]")
async def get_all_customer_interactions_endpoint(
    customer_interaction: CustomerInteractionService = Depends(get_customer_interaction_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    search: Optional[str] = Query(None),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    """
    Endpoint untuk mendapatkan semua interaksi customer dengan pagination.
    Membutuhkan access token dan API key yang valid.
    """
    logger.info(f"[INTERACTION] Fetching interactions offset={offset}, limit={limit}")
    result = customer_interaction.get_all_customer_interactions(client_id, offset, limit, search)

    logger.info(f"[INTERACTION] Fetched total={result['total']}")
    return PaginatedCustomerInteractionResponse(
        total=result["total"],
        data=[
            CustomerInteractionResponse(**jsonable_encoder(row))
            for row in result["data"]
        ]
    )
