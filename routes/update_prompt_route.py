from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.prompt_model import Prompt
from models.update_prompt_schema import PromptUpdate

router = APIRouter()

# Endpoint Update Prompt
@router.put("/prompts/{name}")
def update_prompt(name: str, prompt_update: PromptUpdate, db: Session = Depends(config_db)):
    prompt = db.query(Prompt).filter(Prompt.name == name).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt.content = prompt_update.content
    db.commit()
    return {"message": "Prompt updated successfully"}