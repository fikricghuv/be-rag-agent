from agno.agent import Agent, AgentMemory
from models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb, MemoryDb
from tools.get_instruction import get_instructions_from_db
from config.settings import URL_DB_POSTGRES
from tools.knowledge_base_tools import knowledge_base
from tools.get_knowledge_base_param import get_knowledge_base_config
from agents.product_information_agent.product_information_agent_team import product_information_agent
from agents.feedback_handler_agent.customer_feedback_agent import customer_feedback_agent
from agents.customer_service_agent.prompt_role import role_agent
from agents.customer_service_agent.prompt_instructions import instructions_agent
from agents.general_information_insurance_agent.general_insurance_information_agent import general_insurance_information_agent
from agno.team.team import Team, TeamMemory

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

    customer_service_agent = Team(
        name='Customer Service Team',
        team_id="customer_service_team",
        session_id=session_id,
        user_id=user_id,
        description="You are a Customer Service Agent to provide information about BRI INSURANCE products, services, and policies.",
        instructions=instructions_agent,
        model=openai_model(),
        mode="coordinate",
        members=[product_information_agent, customer_feedback_agent, general_insurance_information_agent],
        debug_mode=True,
        show_tool_calls=True,
        tool_call_limit=3,
        memory=TeamMemory(
            user_id=user_id,
            db=PgMemoryDb(
                table_name="agent_memory", 
                db_url=URL_DB_POSTGRES), 
            create_user_memories=True,
            updating_memory=True,
        ),
        storage=storage,
        markdown=True,
        enable_agentic_context=True,  # Allow the agent to maintain a shared context and send that to members.
        share_member_interactions=True,  # Share all member responses with subsequent member requests.
        show_members_responses=True,
        expected_output="Answer questions from users about BRI INSURANCE products, services, and policies.",
    )

    return customer_service_agent