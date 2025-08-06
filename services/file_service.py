import logging
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import HTTPException, status, Depends, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models.upload_file_model import FileModel
from core.config_db import config_db
from utils.save_file_from_postgres_utils import save_pdfs_locally, delete_pdfs_locally
from agents.tools.knowledge_base_tools import knowledge_base
from schemas.knowledge_base_config_schema import KnowledgeBaseConfig
from utils.get_knowledge_base_param_utils import get_knowledge_base_config
from exceptions.custom_exceptions import DatabaseException, ServiceException
from sqlalchemy import text, desc
from uuid import UUID

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_all_files(self, client_id: UUID) -> List[FileModel]:
        try:
            logger.info("[SERVICE][FILE] Fetching all files from database.")
            files = (
                self.db.query(FileModel)
                .filter(FileModel.client_id == client_id, FileModel.status != 'inactive')
                .order_by(desc(FileModel.uploaded_at))
                .all()
            )
            logger.info(f"[SERVICE][FILE] Successfully fetched {len(files)} files.")
            return files
        
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][FILE] DB error fetching all files: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_FILES_ERROR", message="Failed to fetch files.")

    async def save_file(self, file: UploadFile, client_id: UUID) -> FileModel:
        try:
            logger.info(f"[SERVICE][FILE] Saving file: {file.filename} (size: {file.size})")
            file_content = await file.read()

            if file.content_type not in ["application/pdf", "text/plain"]:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            if file.size and file.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

            file_uuid = uuid.uuid4()
            new_file = FileModel(
                uuid_file=file_uuid,
                filename=file.filename,
                content_type=file.content_type,
                content=file_content,
                size=file.size,
                status='pending',
                client_id=client_id
            )

            self.db.add(new_file)
            self.db.commit()
            self.db.refresh(new_file)

            logger.info(f"[SERVICE][FILE] File saved successfully with UUID: {file_uuid}")
            return new_file

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] DB error saving file: {e}", exc_info=True)
            raise DatabaseException(code="DB_SAVE_FILE_ERROR", message="Failed to save file.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] Unexpected error saving file: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_SAVE_FILE_ERROR", message="Unexpected error occurred while saving file.")

    def delete_file_from_db(self, uuid_file: uuid.UUID, client_id: UUID) -> Dict[str, str]:
        try:
            logger.info(f"[SERVICE][FILE] Deleting file with UUID: {uuid_file} for client_id: {client_id}")
            
            file_to_delete = (
                self.db.query(FileModel)
                .filter(FileModel.uuid_file == uuid_file, FileModel.client_id == client_id)
                .first()
            )

            if not file_to_delete:
                logger.warning(f"[SERVICE][FILE] File not found or does not belong to client_id {client_id}: {uuid_file}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            filename_without_ext = file_to_delete.filename.rsplit('.', 1)[0]

            delete_vector_documents = """
                DELETE FROM ai.ms_vector_documents
                WHERE name = :filename_without_ext
                AND client_id = :client_id
            """
            self.db.execute(
                text(delete_vector_documents),
                {"filename_without_ext": filename_without_ext, "client_id": str(client_id)}
            )

            file_to_delete.status = "inactive"
            self.db.commit()
            logger.info(f"[SERVICE][FILE] File and vector document deleted for: {filename_without_ext} (client_id: {client_id})")

            return {"message": "File and associated vectors deleted successfully"}
        
        except HTTPException:
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] DB error deleting file/vector: {e}", exc_info=True)
            raise DatabaseException(code="DB_DELETE_FILE_VECTOR_ERROR", message="Failed to delete file and vector document.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] Unexpected error deleting file/vector: {e}", exc_info=True)
            raise ServiceException(code="UNEXPECTED_DELETE_FILE_VECTOR_ERROR", message="Unexpected error occurred while deleting file/vector.")

    async def process_embedding(self, client_id: UUID) -> Dict[str, Any]:
        async def _process():
            logger.info(f"[SERVICE][FILE] Starting embedding processing for client_id: {client_id}...")

            pending_files = (
                self.db.query(FileModel)
                .filter(FileModel.status == 'pending', FileModel.client_id == client_id)
                .all()
            )

            if not pending_files:
                logger.info(f"[SERVICE][FILE] No pending files found for client_id: {client_id}.")
                return {
                    "message": "No pending files found for embedding.",
                    "status": "success"
                }
            
            save_pdfs_locally([file.filename for file in pending_files])
            logger.info(f"[SERVICE][FILE] {len(pending_files)} PDFs saved locally for embedding.")

            db_config = get_knowledge_base_config()
            kb_config = KnowledgeBaseConfig(**db_config)
            logger.info(f"[SERVICE][FILE] Knowledge Base Config: {kb_config}")

            kb = knowledge_base(
                chunk_size=kb_config.chunk_size,
                overlap=kb_config.overlap,
                num_documents=kb_config.num_documents,
            )

            kb.load(recreate=False, upsert=True, skip_existing=True)
            logger.info("[SERVICE][FILE] Knowledge base loaded and embeddings processed.")

            updated_rows = (
                self.db.query(FileModel)
                .filter(FileModel.status == 'pending', FileModel.client_id == client_id)
                .update({FileModel.status: 'processed'}, synchronize_session=False)
            )
            self.db.commit()

            logger.info(f"[SERVICE][FILE] {updated_rows} files updated to 'processed' for client_id: {client_id}.")
            
            delete_pdfs_locally([file.filename for file in pending_files])
            logger.info(f"[SERVICE][FILE] {len(pending_files)} PDFs removed locally after embedding.")

            return {
                "message": "Embedding processing completed.",
                "status": "success"
            }

        try:
            return await asyncio.wait_for(_process(), timeout=60)  # Timeout 60 detik
        except asyncio.TimeoutError:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] Embedding processing timed out for client_id: {client_id}.")
            raise ServiceException(code="TIMEOUT_ERROR", message="Embedding processing exceeded 1 minute and was terminated.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"[SERVICE][FILE] Error processing embedding for client {client_id}: {e}", exc_info=True)
            raise ServiceException(code="EMBEDDING_PROCESSING_ERROR", message="Failed to process file embeddings.")

def get_file_service(db: Session = Depends(config_db)) -> FileService:
    return FileService(db)
