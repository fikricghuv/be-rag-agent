from agno.models.openai import OpenAIChat
from config.settings import OPENAI_API_KEY

def openai_model() :
    openai_model = OpenAIChat(
        id='gpt-4o', 
        api_key=OPENAI_API_KEY,  
        temperature=0.3, 
        max_tokens=500,
        )
    return openai_model
