from services.prompt_service import PromptService
from core.config_db import config_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def get_customer_service_prompt_fields(client_id):
    db_gen = config_db()
    db: Session = next(db_gen)
    try:
        prompt_service = PromptService(db)
        prompts = prompt_service.fetch_customer_service_prompt(client_id)
        if not prompts:
            return "", "", "", ""
        prompt = prompts[0]
        return (
            prompt.name_agent or "Default Agent",
            prompt.description_agent or "No description.",
            prompt.prompt_system or "You are a helpful assistant.",
            prompt.goal or "Help the user.",
            prompt.expected_output or "Provide a clear and concise answer."
            # prompt.style_communication or "Be concise.",
            # prompt  # return full prompt if needed
        )
    finally:
        try:
            db_gen.close()
        except Exception:
            pass

