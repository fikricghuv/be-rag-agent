from agno.agent import Agent, AgentMemory
from models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb
from tools.get_instruction import get_instructions_from_db
from config.settings import URL_DB_POSTGRES
from tools.knowledge_base_tools import knowledge_base, knowledge_base_json
from tools.get_knowledge_base_param import get_knowledge_base_config
from agents.product_information_agent.prompt_instructions import instructions_agent
from agno.models.mistral import MistralChat
from agno.tools.duckduckgo import DuckDuckGoTools

instructions_from_db = get_instructions_from_db('Product Information Agent')
kb_config = get_knowledge_base_config()

storage = PostgresAgentStorage(
# store sessions in the ai.sessions table
table_name="agent_sessions",
# db_url: Postgres database URL
db_url=URL_DB_POSTGRES,
)

# Inisialisasi agen

product_information_agent = Agent(
    name='Product Information Agent',
    agent_id="Product-Information-Agent",
    description="You are a helpful Agent called 'Agentic RAG' and your goal is to assist the user in the best way possible.",
    # instructions=instructions_from_db,
    instructions=instructions_agent,
    model=openai_model(),
    tools=[DuckDuckGoTools()],
    # knowledge=knowledge_base(**kb_config), 
    knowledge=knowledge_base_json(),
    search_knowledge=True,
    add_context=True,
    debug_mode=True,
    show_tool_calls=True,
    tool_call_limit=3,
    markdown=True,
)