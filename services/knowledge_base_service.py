# app/services/knowledge_base_service.py
import psycopg2
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT
from models.knowledge_base_config_model import KnowledgeBaseConfig
from fastapi import HTTPException
from utils.get_knowledge_base_param import get_knowledge_base_config
from agents.tools.knowledge_base_tools import knowledge_base

class KnowledgeBaseService:
    def __init__(self):
        pass

    def _get_db_connection(self):
        try:
            return psycopg2.connect(
                dbname=DB_NAME,
                user=USER_DB,
                password=PASSWORD_DB,
                host=HOST,
                port=PORT
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

    def update_knowledge_base_config(self, new_config: KnowledgeBaseConfig) -> KnowledgeBaseConfig:
        if new_config.chunk_size < 1000 or new_config.overlap <= 0 or new_config.num_documents <= 1:
            raise HTTPException(status_code=400, detail="Invalid parameters for knowledge base config")

        connection = self._get_db_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE knowledge_base_config
                        SET chunk_size = %s,
                            overlap = %s,
                            num_documents = %s
                        WHERE id = 1
                    """, (new_config.chunk_size, new_config.overlap, new_config.num_documents))
            return new_config
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
        finally:
            connection.close()

    def retrieve_and_apply_kb_config(self) -> dict:
        db_config = get_knowledge_base_config()
        kb_config = KnowledgeBaseConfig(**db_config)

        _ = knowledge_base(
            chunk_size=kb_config.chunk_size,
            overlap=kb_config.overlap,
            num_documents=kb_config.num_documents,
        )

        return {
            "message": "Knowledge base config retrieved and applied",
            "config": kb_config
        }