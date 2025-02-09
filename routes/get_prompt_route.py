from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.prompt_model import Prompt

router = APIRouter()

# Endpoint Get Prompts
@router.get("/prompts")
def get_prompts(db: Session = Depends(config_db)):
    prompts = db.query(Prompt).all()
    return [{"name": prompt.name, "content": prompt.content} for prompt in prompts]
