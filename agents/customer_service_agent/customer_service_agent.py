from agno.agent import Agent
from agno.tools.postgres import PostgresTools
from agno.tools.telegram import TelegramTools
from agno.storage.postgres import PostgresStorage
from core.settings import (TELEGRAM_BOT_TOKEN, 
                           TELEGRAM_CHAT_ID, 
                           URL_DB_POSTGRES, 
                           SESSION_TABLE_NAME,
                           OPENAI_API_KEY)
from agents.customer_service_agent.prompt import get_customer_service_prompt_fields
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat
from agents.tools.knowledge_base_tools import get_all_urls_from_db, create_combined_knowledge_base
from agents.tools.insert_customer_feedback import insert_customer_feedback

storage = PostgresStorage(table_name=SESSION_TABLE_NAME, db_url=URL_DB_POSTGRES)
storage.upgrade_schema()

def call_customer_service_agent(agent_id, session_id, user_id, client_id):
    name_agent, description_agent, instructions, goal, expected_output = get_customer_service_prompt_fields(client_id)
    
    urls = get_all_urls_from_db(client_id)
    
    knowledge_base = create_combined_knowledge_base(client_id, urls)
    
    agent = Agent(
        name=name_agent,
        description=description_agent,
        goal=goal,
        model=OpenAIChat(id='gpt-5', reasoning_effort='medium', api_key=OPENAI_API_KEY),
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
        knowledge=knowledge_base,
        search_knowledge=True,
        tools=[insert_customer_feedback, TelegramTools(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)],
        show_tool_calls=True,
        instructions=instructions,
        expected_output=expected_output,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=True,
        monitoring=True,
    )
    
    agent.knowledge.load(recreate=False)
    
    return agent