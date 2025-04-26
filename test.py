from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector, SearchType
from config.settings import URL_DB_POSTGRES
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
# Create a knowledge base of PDFs from URLs
pdf_knowledge_base = PDFKnowledgeBase(
        # path="resources/pdf_from_postgres", 
        path="resources/pdf_from_postgres",
        # Table name: ai.pdf_documents
        vector_db=PgVector(
            # table_name="pdf_document_ollama_embedder",
            table_name="pdf_document_embedder_ada_002",
            db_url=URL_DB_POSTGRES,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder()
        ),
        num_documents=5,
    )
# Load the knowledge base: Comment after first run as the knowledge base is already loaded
# knowledge_base.load(upsert=True)

agent = Agent(
    model=OpenAIChat(id="gpt-4o", 
                     api_key=api_key,
                     temperature=0.1,),
    knowledge=pdf_knowledge_base,
    # Add a tool to search the knowledge base which enables agentic RAG.
    # This is enabled by default when `knowledge` is provided to the Agent.
    search_knowledge=True,
    show_tool_calls=True,
    markdown=True,
)
agent.print_response(
    "apa perbedaan asuransi oto dengan sepeda?", stream=True
)