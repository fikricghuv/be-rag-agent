from agno.agent import Agent
from models.openai_model import openai_model
from tools.postgres_tools import postgres_tools
from tools.get_instruction import get_instructions_from_db

instructions_from_db = get_instructions_from_db('Analytics Agent')

def call_analytics_data_agent():

    analytics_data_agent = Agent(
        agent_id="analytics_data_agent",
        name="Analytics Agent", 
        model=openai_model(),
        description="The Analytics Data Agent is responsible for collecting, analyzing, and providing relevant data reports to support decision-making by the Technical Manager Agent.",
        instructions=instructions_from_db,
        prevent_hallucinations=True,
        markdown=True,
        debug_mode=True,
        tools=[postgres_tools],
    )
    return analytics_data_agent