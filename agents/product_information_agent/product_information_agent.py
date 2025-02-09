from agno.agent import Agent, AgentMemory
from models.openai_model import openai_model
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.document.chunking.recursive import RecursiveChunking
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb
from tools.get_instruction import get_instructions_from_db
from config.settings import URL_DB_POSTGRES
from tools.knowledge_base_tools import knowledge_base
from tools.get_knowledge_base_param import get_knowledge_base_config

instructions_from_db = get_instructions_from_db()
kb_config = get_knowledge_base_config()
chunk_size = kb_config['chunk_size']
overlap = kb_config['overlap']
num_documents = kb_config['num_documents']


storage = PostgresAgentStorage(
    # store sessions in the ai.sessions table
    table_name="agent_sessions",
    # db_url: Postgres database URL
    db_url=URL_DB_POSTGRES,
)

# Inisialisasi agen
def call_agent(session_id, user_id) :
    product_information_agent = Agent(
        name='Product Information Agent',
        agent_id="Product-Information-Agent",
        session_id=session_id,
        user_id=user_id,
        description="You are a RAG agent to read BRI INSURANCE product documents",
        instructions=instructions_from_db,
        model=openai_model(),
        knowledge=knowledge_base(chunk_size, overlap, num_documents), 
        search_knowledge=True,
        add_context=True,
        debug_mode=True,
        show_tool_calls=True,
        memory=AgentMemory(
            user_id=user_id,
            db=PgMemoryDb(
                table_name="agent_memory", 
                db_url=URL_DB_POSTGRES), 
            create_user_memories=True, 
            create_session_summary=True,
            updating_memory=True,
        ),
        storage=storage,
        markdown=True,
        add_history_to_messages=True,
        num_history_responses=2,
    )

    return product_information_agent

