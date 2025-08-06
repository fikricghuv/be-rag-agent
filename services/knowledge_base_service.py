import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends, HTTPException, status
from database.models.knowledge_base_config_model import KnowledgeBaseConfigModel 
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
from core.config_db import config_db
from exceptions.custom_exceptions import DatabaseException, ServiceException
from uuid import UUID

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    def get_knowledge_base_config_from_db(self, client_id: UUID) -> KnowledgeBaseConfigModel:
        
        try:
            logger.info(f"[SERVICE][KB] Fetching knowledge base config for client {client_id} from database.")

            config_model = (
                self.db.query(KnowledgeBaseConfigModel)
                .filter(KnowledgeBaseConfigModel.client_id == client_id)
                .first()
            )

            if not config_model:
                logger.warning(f"[SERVICE][KB] Config not found for client {client_id}.")
                raise ServiceException(
                    code="KB_CONFIG_NOT_FOUND",
                    message="Knowledge base config not found for this client.",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            logger.info("[SERVICE][KB] Config successfully fetched.")
            return config_model

        except ServiceException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][KB] DB error fetching config for client {client_id}: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_KB_CONFIG", message="Database error fetching KB config.")
        except Exception as e:
            logger.error(f"[SERVICE][KB] Unexpected error: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_KB_FETCH", message="Unexpected error occurred.")


    def update_knowledge_base_config(self, new_config: KnowledgeBaseConfig, client_id: UUID) -> KnowledgeBaseConfigModel:
        
        if new_config.chunk_size < 100 or new_config.overlap < 0 or new_config.num_documents < 1:
            logger.warning(f"[SERVICE][KB] Invalid config params: {new_config}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parameters for knowledge base config: chunk_size >= 100, overlap >= 0, num_documents >= 1"
            )

        try:
            logger.info(f"[SERVICE][KB] Updating config for client {client_id} with new values: {new_config}")

            config_model = (
                self.db.query(KnowledgeBaseConfigModel)
                .filter(KnowledgeBaseConfigModel.client_id == client_id)
                .first()
            )

            if not config_model:
                logger.warning(f"[SERVICE][KB] Config not found for client {client_id}. Creating new config.")
                config_model = KnowledgeBaseConfigModel(
                    client_id=client_id,
                    chunk_size=new_config.chunk_size,
                    overlap=new_config.overlap,
                    num_documents=new_config.num_documents
                )
                self.db.add(config_model)
            else:
                config_model.chunk_size = new_config.chunk_size
                config_model.overlap = new_config.overlap
                config_model.num_documents = new_config.num_documents

            self.db.commit()
            self.db.refresh(config_model)

            logger.info("[SERVICE][KB] Config updated successfully.")
            return config_model

        except ServiceException:
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][KB] DB error updating config for client {client_id}: {e}", exc_info=True)
            raise DatabaseException(code="DB_UPDATE_KB_CONFIG", message="Database error updating KB config.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][KB] Unexpected error updating config: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_KB_UPDATE", message="Unexpected error occurred while updating KB config.")

def get_knowledge_base_service(db: Session = Depends(config_db)) -> KnowledgeBaseService:
    return KnowledgeBaseService(db)
