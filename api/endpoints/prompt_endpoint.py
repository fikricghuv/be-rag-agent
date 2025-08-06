# app/api/endpoints/prompt_endpoint.py
import logging
from fastapi import APIRouter, Depends, Path
from typing import List
from services.prompt_service import PromptService, get_prompt_service
from schemas.prompt_schema import PromptResponse, PromptUpdate
from middleware.token_dependency import verify_access_token
from utils.exception_handler import handle_exceptions  
from uuid import UUID
from middleware.auth_client_dependency import get_authenticated_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["prompts"])

@router.get("/prompts", response_model=List[PromptResponse])
@handle_exceptions(tag="[PROMPT]")
async def get_prompts_endpoint(
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info("[PROMPT] Fetching all prompts.")
    return prompt_service.fetch_customer_service_prompt(client_id=client_id)

@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
@handle_exceptions(tag="[PROMPT]")
async def update_prompt_endpoint(
    prompt_update: PromptUpdate,
    prompt_id: UUID = Path(..., description="UUID of the prompt to update"),
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[PROMPT] Updating prompt with ID: {prompt_id}")
    return prompt_service.update_prompt(prompt_id, prompt_update, client_id)
