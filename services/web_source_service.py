import logging
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, text
from uuid import UUID
from schemas.website_source_schema import WebsiteUrlPayload
from database.models.web_source_model import WebSourceModel
from core.config_db import config_db
from exceptions.custom_exceptions import DatabaseException, ServiceException
from schemas.website_source_schema import WebsiteKBInfo
from datetime import datetime
from agents.tools.knowledge_base_tools import create_combined_knowledge_base
from database.models.client_model import Client
from core.settings import KNOWLEDGE_WEB_TABLE_NAME

logger = logging.getLogger(__name__)
class WebSourceService:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_subdomain(self, client_id: uuid) -> str:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client with id {client_id} not found")
        
        safe_name = client.subdomain.lower().replace(" ", "_")
        
        return safe_name

    def fetch_all_links(self, client_id: UUID) -> List[WebsiteKBInfo]:
        try:
            logger.info("[SERVICE][WEB] Fetching all links from database.")
            links = (
                self.db.query(WebSourceModel)
                .filter(WebSourceModel.client_id == client_id, WebSourceModel.status != 'inactive')
                .order_by(desc(WebSourceModel.created_at))
                .all()
            )
            logger.info(f"[SERVICE][WEB] Successfully fetched {len(links)} links.")
            return links
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][WEB] DB error fetching all links: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_LINKS_ERROR", message="Failed to fetch web links.")

    def add_link(self, url: WebsiteUrlPayload, client_id: UUID) -> WebSourceModel:
        try:
            logger.info(f"[SERVICE][WEB] Adding new link: {url}")
            new_link = WebSourceModel(
                id=uuid.uuid4(),
                url=url.url,
                status="pending",
                source_type="website",
                created_at=datetime.utcnow(), 
                client_id=client_id
            )

            self.db.add(new_link)
            self.db.commit()
            self.db.refresh(new_link)

            logger.info(f"[SERVICE][WEB] Link saved successfully: {new_link.id}")
            return new_link
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][WEB] DB error adding link: {e}", exc_info=True)
            raise DatabaseException(code="DB_ADD_LINK_ERROR", message="Failed to add web link.")

    def update_status(self, link_id: UUID, client_id: UUID) -> Dict[str, str]:
        try:
            logger.info(f"[SERVICE][WEB] Updating status for link {link_id} to {status}")

            updated_rows = (
                self.db.query(WebSourceModel)
                .filter(WebSourceModel.id == link_id, WebSourceModel.client_id == client_id)
                .update({WebSourceModel.status: status}, synchronize_session=False)
            )

            if updated_rows == 0:
                raise ServiceException(status_code=status.HTTP_404_NOT_FOUND, message="Link not found", code="UPDATE_STATUS")

            self.db.commit()
            logger.info(f"[SERVICE][WEB] Link {link_id} status updated to {status}")
            return {"message": "Link status updated successfully"}
        except HTTPException:
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][WEB] DB error updating status: {e}", exc_info=True)
            raise DatabaseException(code="DB_UPDATE_LINK_STATUS_ERROR", message="Failed to update link status.")

    async def process_embedding(self, client_id: UUID) -> Dict[str, Any]:
        async def _process():
            logger.info(f"[SERVICE][WEB] Starting embedding processing for client_id: {client_id}...")

            pending_links = (
                self.db.query(WebSourceModel)
                .filter(WebSourceModel.status == 'pending', WebSourceModel.client_id == client_id)
                .all()
            )

            if not pending_links:
                logger.info(f"[SERVICE][WEB] No pending links found for client_id: {client_id}.")
                return {"message": "No pending links found for embedding.", "status": "success"}

            urls = [link.url for link in pending_links]
            combined_kb = create_combined_knowledge_base(client_id, urls)
            combined_kb.load(recreate=False, upsert=True, skip_existing=True)
            
            logger.info("[SERVICE][WEB] Web knowledge base loaded and embeddings processed.")

            updated_rows = (
                self.db.query(WebSourceModel)
                .filter(WebSourceModel.status == 'pending', WebSourceModel.client_id == client_id)
                .update({WebSourceModel.status: 'processed'}, synchronize_session=False)
            )
            self.db.commit()

            logger.info(f"[SERVICE][WEB] {updated_rows} links updated to 'processed' for client_id: {client_id}.")

            return {"message": "Web link embedding processing completed.", "status": "success"}

        try:
            return await asyncio.wait_for(_process(), timeout=60)
        except asyncio.TimeoutError:
            self.db.rollback()
            logger.error(f"[SERVICE][WEB] Embedding processing timed out for client_id: {client_id}.")
            raise ServiceException(status_code=408, code="TIMEOUT_ERROR", message="Embedding processing exceeded 1 minute and was terminated.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][WEB] Error processing web link embedding for client {client_id}: {e}", exc_info=True)
            raise ServiceException(code="WEB_EMBEDDING_PROCESSING_ERROR", message="Failed to process web link embeddings.")

    def delete_link_by_id(self, url_id: UUID, client_id: UUID) -> dict:
        """
        Delete link from database by its UUID and client_id.
        Instead of physically deleting, we can mark as inactive.
        """
        try:
            logger.info(f"[SERVICE][WEB] Deleting link UUID: {url_id} for client {client_id}")

            link = (
                self.db.query(WebSourceModel)
                .filter(WebSourceModel.id == url_id, WebSourceModel.client_id == client_id)
                .first()
            )

            if not link:
                logger.warning(f"[SERVICE][WEB] Link not found for UUID: {url_id}")
                raise DatabaseException(code="LINK_NOT_FOUND", message="Link not found.")

            filename_without_ext = link.url
            logger.info(f"[SERVICE][WEB] Name url to delete: {filename_without_ext}")

            table_name = self._get_subdomain(client_id)

            if link.status != "pending":
                delete_vector_documents = f"""
                    DELETE FROM ai.{KNOWLEDGE_WEB_TABLE_NAME}_{table_name}
                    WHERE name = :filename_without_ext
                """
                self.db.execute(
                    text(delete_vector_documents),
                    {"filename_without_ext": filename_without_ext}
                )
                logger.info(f"[SERVICE][WEB] Deleted vector document for: {filename_without_ext}")
            else:
                logger.info(f"[SERVICE][WEB] Skipping vector delete because status is 'pending'")

            link.status = "inactive"
            self.db.commit()

            logger.info(f"[SERVICE][WEB] Successfully deleted link UUID: {url_id}")
            return {"message": "Link deleted successfully", "url_id": url_id}

        except Exception as e:
            logger.exception(f"[SERVICE][WEB] Error deleting link UUID: {url_id} - {str(e)}")
            self.db.rollback()
            raise


        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][WEB] DB error deleting link: {e}", exc_info=True)
            raise DatabaseException(code="DB_DELETE_LINK_ERROR", message="Failed to delete link.")
        
def get_web_source_service(db: Session = Depends(config_db)) -> WebSourceService:
    return WebSourceService(db)
