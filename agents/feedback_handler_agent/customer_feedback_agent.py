from phi.agent import Agent
from models.openai_model import openai_model
from tools.postgres_tools import postgres_tools
from tools.insert_data_feedback_tools import PostgresInsertToolkit

connection_params = {
    "host": "localhost",
    "port": 5532,
    "dbname": "ai",
    "user": "ai",
    "password": "ai"
}

insert_postgres_toolkit = PostgresInsertToolkit(connection_params)

customer_feedback_agent = Agent(
    name='Customer Feedback Agent',
    agent_id="customer_feedback_agent",
    description="Handles customer feedback, analyzes sentiment, and provides actionable insights.",
    instructions=[
        "Show empathy to customers for the problems they have",
        "Analyze the feedback for sentiment (positive, negative, neutral).",
        "Extract key topics or issues mentioned in the feedback.",
        "Suggest potential actions or improvements based on the feedback.",
        "Insert the processed feedback, along with the analysis results, into the PostgreSQL database with insert_postgres_toolkit."
    ],
    model=openai_model(),
    tools=[insert_postgres_toolkit], #postgres_tools
    tool_call_limit=3,
    show_tool_calls=True,
)
