from agno.models.openai import OpenAIChat
from config.settings import OPENAI_API_KEY

def openai_model(temperature=0.1, max_tokens=300) :
    openai_model = OpenAIChat(
        id='gpt-4o', 
        api_key=OPENAI_API_KEY,  
        temperature=temperature, 
        max_tokens=max_tokens,
        )
    return openai_model
