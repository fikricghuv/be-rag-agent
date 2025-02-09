from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.document.chunking.recursive import RecursiveChunking
from config.settings import URL_DB_POSTGRES


def knowledge_base (chunk_size, overlap, num_documents):
    pdf_knowledge_base = PDFKnowledgeBase(
        path="resources/pdf_from_postgres",
        # Table name: ai.pdf_documents
        vector_db=PgVector(
            table_name="pdf_document_ollama_embedder",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            embedder=OllamaEmbedder(id="openhermes")
        ),
        chunking_strategy=RecursiveChunking(
            # chunk_size=3000,
            # overlap=200,
            chunk_size=chunk_size,
            overlap=overlap,
        ),
        
        # num_documents=3,
        num_documents=num_documents,
        reader=PDFReader(),
    )

    return pdf_knowledge_base