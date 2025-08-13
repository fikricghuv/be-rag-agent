from fastapi import APIRouter, Depends, status, Body
from typing import List
from uuid import UUID
import logging
from services.web_source_service import WebSourceService, get_web_source_service
from schemas.website_source_schema import WebsiteKBInfo, WebsiteKBCreateResponse, WebsiteUrlPayload
from middleware.token_dependency import verify_access_token_and_get_client_id
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["website-knowledge-base"])

@router.get("/website-source", response_model=List[WebsiteKBInfo])
@handle_exceptions(tag="[WEBSITE_KB]")
async def get_all_website_kb_endpoint(
    kb_service: WebSourceService = Depends(get_web_source_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[WEBSITE_KB] Fetching website KB for client_id={client_id}")
    return kb_service.fetch_all_links(client_id=client_id)

@router.post(
    "/website-source",
    response_model=WebsiteKBCreateResponse,
    status_code=status.HTTP_201_CREATED
)
@handle_exceptions(tag="[WEBSITE_KB]")
async def create_website_kb_endpoint(
    url: WebsiteUrlPayload,
    kb_service: WebSourceService = Depends(get_web_source_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[WEBSITE_KB] Creating new website KB for client_id={client_id} with {url} urls")
    result = kb_service.add_link(url=url, client_id=client_id)
    return WebsiteKBCreateResponse(
        message="Website knowledge base created successfully",
        url=result.url
    )

@router.delete("/website-source/{url_id}")
@handle_exceptions(tag="[WEBSITE_KB]")
async def delete_website_by_id_endpoint(
    url_id: UUID,
    kb_service: WebSourceService = Depends(get_web_source_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[WEBSITE_KB] Deleting all KB data for client_id={client_id}")
    return kb_service.delete_link_by_id(url_id=url_id, client_id=client_id)

@router.post("/website-source/process-embedding")
@handle_exceptions(tag="[WEBSITE_KB]")
async def process_website_kb_embedding_endpoint(
    kb_service: WebSourceService = Depends(get_web_source_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[WEBSITE_KB] Processing website KB embedding for client_id={client_id}")
    return await kb_service.process_embedding(client_id=client_id)
