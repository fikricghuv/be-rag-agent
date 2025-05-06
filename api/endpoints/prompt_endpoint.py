# app/api/endpoints/prompt_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.config_db import config_db
from models.prompt_model import PromptResponse  # Assuming you have a response schema
from services.prompt_service import PromptService
from typing import List
from schemas.update_prompt_schema import PromptUpdate

router = APIRouter()

def get_prompt_service(db: Session = Depends(config_db)):
    return PromptService(db)

@router.get("/prompts", response_model=List[PromptResponse])
def get_prompts_endpoint(prompt_service: PromptService = Depends(get_prompt_service)):
    try:
        return prompt_service.fetch_all_prompts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prompts: {str(e)}")
    
@router.put("/prompts/{name}", response_model=PromptResponse)
def update_prompt_endpoint(
    name: str,
    prompt_update: PromptUpdate,
    prompt_service: PromptService = Depends(get_prompt_service)
):
    try:
        return prompt_service.update_prompt(name, prompt_update)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")