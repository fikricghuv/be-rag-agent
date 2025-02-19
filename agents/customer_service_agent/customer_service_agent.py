from agno.agent import Agent, AgentMemory
from models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb
from tools.get_instruction import get_instructions_from_db
from config.settings import URL_DB_POSTGRES
from tools.knowledge_base_tools import knowledge_base
from tools.get_knowledge_base_param import get_knowledge_base_config
from models.gemini_model import gemini_model
from agents.product_information_agent import product_information_agent
from agents.feedback_handler_agent import customer_feedback_agent

instructions_from_db = get_instructions_from_db('Customer Service Agent')
kb_config = get_knowledge_base_config()

storage = PostgresAgentStorage(
    # store sessions in the ai.sessions table
    table_name="agent_sessions",
    # db_url: Postgres database URL
    db_url=URL_DB_POSTGRES,
)

# Inisialisasi agen
def call_agent(session_id, user_id) :
    product_information_agent = Agent(
        name='Customer Service Agent',
        agent_id="customer_service_agent",
        session_id=session_id,
        user_id=user_id,
        description="You are a Customer Service Agent to provide information about BRI INSURANCE products, services, and policies.",
        instructions=instructions_from_db,
        model=openai_model(),
        # model=gemini_model(),
        team=[product_information_agent, customer_feedback_agent],
        debug_mode=True,
        show_tool_calls=True,
        tool_call_limit=3,
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

