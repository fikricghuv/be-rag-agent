from fastapi import HTTPException
from sqlalchemy.orm import Session
from database.models.prompt_model import Prompt
from schemas.update_prompt_schema import PromptUpdate
from typing import List

# Function to update prompt in the database
def update_prompt_in_db(name: str, prompt_update: PromptUpdate, db: Session):
    prompt = db.query(Prompt).filter(Prompt.name == name).first()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Update prompt content
    prompt.content = prompt_update.content
    db.commit()
    db.refresh(prompt)  # Optional: Refresh the object to reflect the updated state


def fetch_all_prompts(db: Session) -> List[dict]:
    prompts = db.query(Prompt).all()
    return [{"name": prompt.name, "content": prompt.content} for prompt in prompts]
