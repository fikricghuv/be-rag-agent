from agno.agent import Agent
from models.openai_model import openai_model
from tools.postgres_tools import postgres_tools
from tools.insert_data_feedback_tools import PostgresInsertToolkit
from tools.get_instruction import get_instructions_from_db

insert_postgres_toolkit = PostgresInsertToolkit()
instructions_from_db = get_instructions_from_db('Customer Feedback Agent')

def call_customer_feedback_agent(): 
    customer_feedback_agent = Agent(
        name='Customer Feedback Agent',
        agent_id="customer_feedback_agent",
        description="Handles customer feedback, analyzes sentiment, and provides actionable insights.",
        instructions=instructions_from_db,
        model=openai_model(),
        tools=[insert_postgres_toolkit], #postgres_tools
        tool_call_limit=3,
        show_tool_calls=True,
    )
    return customer_feedback_agent