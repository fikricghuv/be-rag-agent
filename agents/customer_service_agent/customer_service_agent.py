from agno.agent import Agent
from agno.tools.postgres import PostgresTools
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.tools.baidusearch import BaiduSearchTools
from agno.tools.telegram import TelegramTools
from agno.storage.postgres import PostgresStorage
from agents.models.openai_model import openai_model
from agents.models.gemini_model import gemini_model
from core.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, URL_DB_POSTGRES, SESSION_TABLE_NAME, KNOWLEDGE_TABLE_NAME, HOST, PORT, DB_NAME, USER_DB, PASSWORD_DB, SCHEMA_TABLE, OPENAI_API_KEY
from agents.customer_service_agent.prompt import prompt_agent, get_customer_service_prompt_fields
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat

storage = PostgresStorage(table_name=SESSION_TABLE_NAME, db_url=URL_DB_POSTGRES)
storage.upgrade_schema()

knowledge_base = PDFKnowledgeBase(
    path="app/resources/pdf_from_postgres",
    vector_db=PgVector(
        embedder=OpenAIEmbedder(),
        table_name=KNOWLEDGE_TABLE_NAME,
        db_url=URL_DB_POSTGRES,
        search_type=SearchType.hybrid,
        content_language="indonesian",
    ),
)

postgres_tools = PostgresTools(
    host=HOST,
    port=PORT,
    db_name=DB_NAME,
    user=USER_DB,
    password=PASSWORD_DB,
    table_schema=SCHEMA_TABLE
)

def call_customer_service_agent(agent_id, session_id, user_id, client_id):
    name_agent, description_agent = get_customer_service_prompt_fields(client_id)
    
    agent = Agent(
        name=name_agent,
        description=description_agent,
        # model=openai_model(temperature=0.3, max_tokens=1000),
        model=OpenAIChat(id='gpt-5', reasoning_effort='low', api_key=OPENAI_API_KEY),
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
        knowledge=knowledge_base, 
        show_tool_calls=True,
        search_knowledge=True,
        tools=[postgres_tools, TelegramTools(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)],
        instructions=prompt_agent(client_id=client_id),
        
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,

        add_datetime_to_instructions=True,

        markdown=True,
        debug_mode=True,
    )
    
    return agent