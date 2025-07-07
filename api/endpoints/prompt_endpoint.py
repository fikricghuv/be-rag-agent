# app/api/endpoints/prompt_endpoint.py
import logging
from fastapi import APIRouter, Depends, Path
from typing import List
from services.prompt_service import PromptService, get_prompt_service
from middleware.verify_api_key_header import api_key_auth
from schemas.prompt_schema import PromptResponse, PromptUpdate
from middleware.token_dependency import verify_access_token
from utils.exception_handler import handle_exceptions  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["prompts"])

@router.get("/prompts", response_model=List[PromptResponse], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[PROMPT]")
async def get_prompts_endpoint(
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info("[PROMPT] Fetching all prompts.")
    return prompt_service.fetch_customer_service_prompt()

@router.put("/prompts/{name}", response_model=PromptResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[PROMPT]")
async def update_prompt_endpoint(
    prompt_update: PromptUpdate,
    name: str = Path(..., description="Name of the prompt to update"),
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info(f"[PROMPT] Updating prompt with name: {name}")
    return prompt_service.update_prompt(name, prompt_update)
