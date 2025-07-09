import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends, status, HTTPException
from datetime import datetime
from uuid import UUID
from database.models.prompt_model import Prompt
from schemas.prompt_schema import PromptUpdate
from core.config_db import config_db
from exceptions.custom_exceptions import DatabaseException, ServiceException

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_all_prompts(self) -> List[Prompt]:
        try:
            logger.info("[SERVICE][PROMPT] Fetching all prompts from database.")
            prompts = self.db.query(Prompt).all()
            logger.info(f"[SERVICE][PROMPT] Successfully fetched {len(prompts)} prompts.")
            return prompts
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][PROMPT] DB error fetching all prompts: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_PROMPTS", message="Failed to fetch prompts from database.")
        except Exception as e:
            logger.error(f"[SERVICE][PROMPT] Unexpected error fetching all prompts: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_PROMPT_FETCH", message="Unexpected error occurred fetching prompts.")

    def fetch_customer_service_prompt(self) -> List[Prompt]:
        try:
            logger.info("[SERVICE][PROMPT] Fetching prompt 'Customer Service Agent' from database.")
            prompts = self.db.query(Prompt).all()
            return prompts
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][PROMPT] DB error fetching customer service prompt: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_CS_PROMPT", message="Failed to fetch customer service prompt.")
        except Exception as e:
            logger.error(f"[SERVICE][PROMPT] Unexpected error fetching CS prompt: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_FETCH_CS_PROMPT", message="Unexpected error occurred.")

    def update_prompt(self, prompt_id: UUID, prompt_update: PromptUpdate) -> Prompt:
        try:
            logger.info(f"[SERVICE][PROMPT] Attempting to update prompt with ID: {prompt_id}")
            prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()

            if not prompt:
                logger.warning(f"[SERVICE][PROMPT] Prompt with ID '{prompt_id}' not found.")
                raise ServiceException(
                    code="PROMPT_NOT_FOUND",
                    message="Prompt not found.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            if prompt_update.name:
                prompt.name = prompt_update.name
            if prompt_update.style_communication:
                prompt.style_communication = prompt_update.style_communication
            if prompt_update.name_agent:
                prompt.name_agent = prompt_update.name_agent
            if prompt_update.description_agent:
                prompt.description_agent = prompt_update.description_agent

            prompt.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(prompt)

            logger.info(f"[SERVICE][PROMPT] Prompt '{prompt_id}' updated successfully.")
            return prompt

        except ServiceException:
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][PROMPT] DB error updating prompt '{prompt_id}': {e}", exc_info=True)
            raise DatabaseException(code="DB_UPDATE_PROMPT", message="Failed to update prompt in database.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][PROMPT] Unexpected error updating prompt '{prompt_id}': {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_PROMPT_UPDATE", message="Unexpected error occurred.")


def get_prompt_service(db: Session = Depends(config_db)) -> PromptService:
    return PromptService(db)
