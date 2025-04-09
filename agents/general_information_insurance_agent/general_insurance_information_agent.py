from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from models.openai_model import openai_model
from textwrap import dedent

general_insurance_information_agent = Agent(
    name='General Inusrance Information Agent',
    agent_id="general_insurance_information_agent",
    # description="Anda adalah Agen General Inusrance Informasi Produk yang memberikan detail tentang definisi umum asuransi",
    role="Provide general information related to insurance.",
    model=openai_model(temperature=0.1),
    # tools=[DuckDuckGoTools()],
    instructions=dedent("""
        Receive general insurance-related questions forwarded from the Customer Service Agent.​

        Offer clear and informative explanations about basic insurance concepts, terminology, and general procedures.​

        If a question falls outside the scope of general information, direct the customer to the appropriate source or agent.
        """),
    debug_mode=True,
    show_tool_calls=True,
    goal="Provide general information related to insurance.",
)