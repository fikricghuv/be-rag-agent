from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.document.chunking.recursive import RecursiveChunking
from agno.document.chunking.fixed import FixedSizeChunking
from core.settings import URL_DB_POSTGRES
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.knowledge.json import JSONKnowledgeBase


def knowledge_base (chunk_size, overlap, num_documents):
    pdf_knowledge_base = PDFKnowledgeBase(
        path="resources/pdf_from_postgres",
        # Table name: ai.pdf_documents
        vector_db=PgVector(
            table_name="vector_documents",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder()
        ),
        num_documents=5,
    )

    return pdf_knowledge_base

def knowledge_base_json ():
    json_knowledge_base = JSONKnowledgeBase(
        path="resources/json_document_insurance",
        vector_db=PgVector(
            table_name="vector_documents",
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