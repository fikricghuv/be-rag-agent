import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends, status
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

    def fetch_all_prompts(self, client_id: UUID) -> List[Prompt]:
        try:
            logger.info(f"[SERVICE][PROMPT] Fetching all prompts for client_id={client_id}")
            prompts = self.db.query(Prompt).filter(Prompt.client_id == client_id).all()
            logger.info(f"[SERVICE][PROMPT] Successfully fetched {len(prompts)} prompts.")
            return prompts
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][PROMPT] DB error fetching all prompts: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_PROMPTS", message="Failed to fetch prompts from database.")

    def fetch_customer_service_prompt(self, client_id: UUID) -> List[Prompt]:
        try:
            logger.info(f"[SERVICE][PROMPT] Fetching 'Customer Service Agent' prompt for client_id={client_id}")
            prompts = (
                self.db.query(Prompt)
                # .filter(Prompt.name.ilike("Customer Service Agent1"))
                .filter(Prompt.client_id == client_id)
                .all()
            )
            return prompts
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][PROMPT] DB error fetching CS prompt: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_CS_PROMPT", message="Failed to fetch customer service prompt.")

    def update_prompt(self, prompt_id: UUID, prompt_update: PromptUpdate, client_id: UUID) -> Prompt:
        try:
            logger.info(f"[SERVICE][PROMPT] Updating prompt {prompt_id} for client_id={client_id}")
            prompt = (
                self.db.query(Prompt)
                .filter(Prompt.id == prompt_id
                        # , Prompt.client_id == client_id
                        )
                .first()
            )

            if not prompt:
                logger.warning(f"[SERVICE][PROMPT] Prompt {prompt_id} not found or unauthorized.")
                raise ServiceException(
                    code="PROMPT_NOT_FOUND",
                    message="Prompt not found or access denied.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            for field, value in prompt_update.dict(exclude_unset=True).items():
                setattr(prompt, field, value)

            prompt.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(prompt)

            logger.info(f"[SERVICE][PROMPT] Prompt '{prompt_id}' updated successfully.")
            return prompt

        except ServiceException:
            self.db.rollback()
            raise ServiceException(code="UPDATE_PROMPT", message="Unexpected error occurred while updating prompt.")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][PROMPT] DB error updating prompt '{prompt_id}': {e}", exc_info=True)
            raise DatabaseException(code="DB_UPDATE_PROMPT", message="Failed to update prompt in database.")

def get_prompt_service(db: Session = Depends(config_db)) -> PromptService:
    return PromptService(db)
