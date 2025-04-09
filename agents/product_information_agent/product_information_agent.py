from agno.agent import Agent
from models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from tools.get_instruction_from_db import get_instructions_from_db
from config.settings import URL_DB_POSTGRES, OPEN_ROUTER_API_KEY
from tools.knowledge_base_tools import knowledge_base, knowledge_base_json
from tools.get_knowledge_base_param import get_knowledge_base_config
from agno.models.openrouter import OpenRouter

instructions_from_db = get_instructions_from_db('Product Information Agent')
kb_config = get_knowledge_base_config()

storage = PostgresAgentStorage(
# store sessions in the ai.sessions table
table_name="agent_sessions",
# db_url: Postgres database URL
db_url=URL_DB_POSTGRES,
)

product_information_agent = Agent(
    name='Product Information Agent',
    agent_id="Product-Information-Agent",
    role="Provide detailed information about BRI INSURANCE products from knowledge base.",
    model=openai_model(max_tokens=1000),
    # model=OpenRouter(id="anthropic/claude-3.7-sonnet", api_key=OPEN_ROUTER_API_KEY),
    knowledge=knowledge_base(**kb_config), 
    # knowledge=knowledge_base_json(),
    search_knowledge=True,
    # add_context=True,
    debug_mode=True,
    show_tool_calls=True,
    # tool_call_limit=3,
    markdown=True,
    goal="Provide detailed information about BRI INSURANCE products based on data.",
)