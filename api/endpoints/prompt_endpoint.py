# app/api/endpoints/prompt_endpoint.py
import logging 
from fastapi import APIRouter, Depends, HTTPException, status, Path 
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError 
from services.prompt_service import PromptService, get_prompt_service 
from middleware.verify_api_key_header import api_key_auth 
from schemas.prompt_schema import PromptResponse, PromptUpdate
from typing import List
from middleware.token_dependency import verify_access_token
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["prompts"], 
)

@router.get("/prompts", response_model=List[PromptResponse], dependencies=[Depends(api_key_auth)])
async def get_prompts_endpoint(
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan semua prompt.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get all prompts.")
        
        prompts =prompt_service.fetch_customer_service_prompt()
        logger.info(f"Returning {len(prompts)} prompts.")
        
        return prompts
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_prompts_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching prompts."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in get_prompts_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.put("/prompts/{name}", response_model=PromptResponse, dependencies=[Depends(api_key_auth)])
async def update_prompt_endpoint(
    prompt_update: PromptUpdate,
    name: str = Path(..., description="Name of the prompt to update"),
    prompt_service: PromptService = Depends(get_prompt_service),
    access_token: str = Depends(verify_access_token) 
):


    """
    Endpoint untuk memperbarui prompt berdasarkan nama.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        name: Nama prompt yang akan diperbarui.
        prompt_update: Data pembaruan prompt (hanya konten).
    """
    try:
        logger.info(f"Received request to update prompt with name: {name}")
        updated_prompt = prompt_service.update_prompt(name, prompt_update)

        logger.info(f"Prompt with name {name} updated successfully.")
        
        return updated_prompt

    except HTTPException as e:
        logger.warning(f"HTTPException raised during prompt update for name {name}: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in update_prompt_endpoint for name {name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

