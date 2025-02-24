from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.document.chunking.recursive import RecursiveChunking
from agno.document.chunking.fixed import FixedSizeChunking
from config.settings import URL_DB_POSTGRES
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.knowledge.json import JSONKnowledgeBase


def knowledge_base (chunk_size, overlap, num_documents):
    pdf_knowledge_base = PDFKnowledgeBase(
        # path="resources/pdf_from_postgres",
        path="resources/json_document_insurance",
        # Table name: ai.pdf_documents
        vector_db=PgVector(
            # table_name="pdf_document_ollama_embedder",
            table_name="json_document_embedder_ada_002",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            # embedder=OllamaEmbedder(id="openhermes")
            embedder=OpenAIEmbedder(id="text-embedding-ada-002", dimensions=1536),
            # embedder=OpenAIEmbedder()

        ),
        # vector_db=LanceDb(
        # table_name="product_information",
        # uri="tmp/lancedb",
        # search_type=SearchType.keyword,
        # embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        # ),
        # chunking_strategy=RecursiveChunking(
        #     # chunk_size=3000,
        #     # overlap=200,
        #     chunk_size=chunk_size,
        #     overlap=overlap,
        # ),
        num_documents=3,
    )

    return pdf_knowledge_base

def knowledge_base_json ():
    json_knowledge_base = JSONKnowledgeBase(
        path="resources/json_document_insurance",
        # Table name: ai.pdf_documents
        vector_db=PgVector(
            table_name="json_document_embedder_ada_002",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            # embedder=OllamaEmbedder(id="openhermes")
            embedder=OpenAIEmbedder(id="text-embedding-ada-002", dimensions=1536),
            
        ),
        chunking_strategy=RecursiveChunking(
            # chunk_size=2000,
            # overlap=200,
        ),
        num_documents=3,
    )

    return json_knowledge_base