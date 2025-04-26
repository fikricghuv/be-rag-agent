from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from controllers.prompt_controller import update_prompt_in_db
from models.update_prompt_schema import PromptUpdate
from config.config_db import config_db

router = APIRouter()

# Endpoint Update Prompt
@router.put("/prompts/{name}")
def update_prompt(name: str, prompt_update: PromptUpdate, db: Session = Depends(config_db)):
    try:
        update_prompt_in_db(name, prompt_update, db)
        return {"message": "Prompt updated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
