from models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb, MemoryDb
from tools.get_instruction_from_db import get_instructions_from_db
from config.settings import URL_DB_POSTGRES, OPEN_ROUTER_API_KEY
from tools.get_knowledge_base_param import get_knowledge_base_config
from agents.product_information_agent.product_information_agent import product_information_agent
from agents.feedback_handler_agent.customer_feedback_agent import customer_feedback_agent
from agents.general_information_insurance_agent.general_insurance_information_agent import general_insurance_information_agent
from agno.team.team import Team, TeamMemory
from textwrap import dedent
from agno.models.openrouter import OpenRouter

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
        members=[product_information_agent, customer_feedback_agent, general_insurance_information_agent], #
        # mode="coordinate",
        mode="route",
        # model=openai_model(),
        model=OpenRouter(id="anthropic/claude-3.7-sonnet", api_key=OPEN_ROUTER_API_KEY),
        name='Customer Service Team',
        team_id="customer_service_team",
        user_id=user_id,
        session_id=session_id,
        description="You are a Customer Service Team to delegate question and information about BRI INSURANCE products to appropriate agent.",
        # instructions=instructions_from_db,
        instructions=dedent("""
            Analyze customer inquiries or feedback and direct them to the appropriate agent.

            Identify the type of request:​

            If related to BRI INSURANCE product information, forward it to the Product Information Agent.​

            If it involves problem/issue, feedback, complaints, or suggestions, forward it to the Feedback Handler Agent.​

            If it is a general question about insurance, forward it to the General Information Agent.​

            Ensure each request is directed accurately and efficiently to maintain customer satisfaction.
            
            Give answer as human as possible not as a robot.
                            
            If the question is not related to BRI INSURANCE, please dont answer it.
            """),
        debug_mode=True,
        show_tool_calls=True,
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
        # share_member_interactions=True,  # Share all member responses with subsequent member requests.
        # show_members_responses=True,
        read_team_history=True,
        enable_team_history=True,
        telemetry=False,
        # expected_output="Delegate task to appropriate agent.",
    )

    return customer_service_agent