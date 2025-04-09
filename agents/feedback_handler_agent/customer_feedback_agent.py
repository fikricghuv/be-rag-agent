from agno.agent import Agent
from models.openai_model import openai_model
from tools.get_instruction_from_db import get_instructions_from_db
from config.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT, SCHEMA_TABLE, OPEN_ROUTER_API_KEY
from textwrap import dedent
from agno.models.openrouter import OpenRouter
instructions_from_db = get_instructions_from_db('Customer Feedback Agent')

from agno.tools.postgres import PostgresTools

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=HOST,
    port=PORT,
    db_name=DB_NAME,
    user=USER_DB,
    password=PASSWORD_DB,
    table_schema=SCHEMA_TABLE,
)

query_sql = """
INSERT INTO ai.customer_feedback(
        id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user)
        VALUES (id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user);
"""

customer_feedback_agent = Agent(
    name='Customer Feedback Agent',
    agent_id="customer_feedback_agent",
    # description="Handles customer feedback, analyzes sentiment, and provides actionable insights.",
    role="Record and analyze customer feedback/complaints.​",
    # instructions=instructions_agent,
    instructions=dedent("""
        Receive feedback, complaints or suggestions forwarded from Customer Service Agents.​

        Get details data from the feedback, like customer name, email address, policy number(if any), claim number(if any), and explain the problem before processing it.​

        run tools postgres_tools to Save feedback, complaints or suggestions data to postgres db with postgres_tools on table customer_feedback according to its columns.
        
        Save all kinds feedback/complaints from customer not only issue claim/policy.
                        
        use this query INSERT INTO ai.customer_feedback(
        id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user)
        VALUES (id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user); 
        
        to insert the data to the table customer_feedback.​
        """),
    # role=role_agent,
    # model=openai_model(),
    model=OpenRouter(id="anthropic/claude-3.7-sonnet", api_key=OPEN_ROUTER_API_KEY),
    # tools=[insert_postgres_toolkit], #postgres_tools
    tools=[postgres_tools.run_query],
    tool_call_limit=3,
    show_tool_calls=True,
    add_context=True,
    debug_mode=True,
    markdown=True,
    add_history_to_messages=True,
    goal="Record data, analyze customer feedback, complaints, or suggestions.",
)
