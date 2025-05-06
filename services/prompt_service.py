# app/services/prompt_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database.models.prompt_model import Prompt
from schemas.update_prompt_schema import PromptUpdate
from typing import List

class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def update_prompt(self, name: str, prompt_update: PromptUpdate):
        prompt = self.db.query(Prompt).filter(Prompt.name == name).first()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        prompt.content = prompt_update.content
        self.db.commit()
        self.db.refresh(prompt)
        return {"name": prompt.name, "content": prompt.content}

    def fetch_all_prompts(self) -> List[dict]:
        prompts = self.db.query(Prompt).all()
        return [{"name": prompt.name, "content": prompt.content} for prompt in prompts]