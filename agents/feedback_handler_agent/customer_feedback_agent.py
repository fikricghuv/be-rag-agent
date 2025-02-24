from agno.agent import Agent
from models.openai_model import openai_model
from tools.insert_data_feedback_tools import PostgresInsertToolkit
from tools.get_instruction import get_instructions_from_db
from agents.feedback_handler_agent.prompt_instructions import instructions_agent
from agents.feedback_handler_agent.prompt_role import role_agent
from config.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT

connection_params = {
    "host": HOST,
    "port": PORT,
    "dbname": DB_NAME,
    "user": USER_DB,
    "password": PASSWORD_DB
}

insert_postgres_toolkit = PostgresInsertToolkit(connection_params)
instructions_from_db = get_instructions_from_db('Customer Feedback Agent')

customer_feedback_agent = Agent(
    name='Customer Feedback Agent',
    agent_id="customer_feedback_agent",
    description="Handles customer feedback, analyzes sentiment, and provides actionable insights.",
    instructions=instructions_agent,
    role=role_agent,
    model=openai_model(),
    tools=[insert_postgres_toolkit], #postgres_tools
    tool_call_limit=3,
    show_tool_calls=True,
)
