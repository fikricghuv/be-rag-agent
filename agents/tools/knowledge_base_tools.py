from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.document.chunking.recursive import RecursiveChunking
from agno.vectordb.lancedb import SearchType
from agno.knowledge.json import JSONKnowledgeBase
from database.models.web_source_model import WebSourceModel
from core.config_db import config_db
from typing import List
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from core.settings import (
    URL_DB_POSTGRES,
    KNOWLEDGE_TABLE_NAME,
    KNOWLEDGE_WEB_TABLE_NAME,
    COMBINED_KNOWLEDGE_TABLE_NAME,
)

def pdf_knowledge_base ():
    knowledge_base_pdf = PDFKnowledgeBase(
        path="resources/pdf_from_postgres",
        vector_db=PgVector(
            # table_name=KNOWLEDGE_TABLE_NAME,
            table_name=COMBINED_KNOWLEDGE_TABLE_NAME,
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder()
        ),
        num_documents=5,
    )

    return knowledge_base_pdf

def knowledge_base_json ():
    json_knowledge_base = JSONKnowledgeBase(
        path="resources/json_document_insurance",
        vector_db=PgVector(
            table_name="ms_vector_documents",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.vector,
            embedder=OpenAIEmbedder(),
            
        ),
        chunking_strategy=RecursiveChunking(
            # chunk_size=2000,
            # overlap=200,
        ),
        num_documents=3,
    )

    return json_knowledge_base

def get_all_urls_from_db(client_id: str):
    """Ambil semua URL dari database berdasarkan client_id."""
    db = next(config_db())
    try:
        url_records = (
                db.query(WebSourceModel)
                .filter(WebSourceModel.status == 'pending', WebSourceModel.client_id == client_id)
                .all()
            )
        return [rec.url for rec in url_records]
    finally:
        db.close()

def create_website_knowledge_base(urls: List[str]) -> WebsiteKnowledgeBase:
    return WebsiteKnowledgeBase(
        urls=urls,
        max_links=5,
        vector_db=PgVector(
            table_name=KNOWLEDGE_WEB_TABLE_NAME,
            db_url=URL_DB_POSTGRES,
        ),
    )

def create_combined_knowledge_base(urls: List[str]) -> CombinedKnowledgeBase:
    website_kb = create_website_knowledge_base(urls)
    pdf_kb = pdf_knowledge_base()
    return CombinedKnowledgeBase(
        sources=[pdf_kb, website_kb],
        vector_db=PgVector(
            table_name=COMBINED_KNOWLEDGE_TABLE_NAME,
            db_url=URL_DB_POSTGRES,
        ),
    )
