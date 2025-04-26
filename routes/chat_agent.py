from fastapi import APIRouter, HTTPException
from agents.customer_service_team.customer_service_team import call_agent
from pydantic import BaseModel
import re

router = APIRouter()

# Pydantic models
class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

# Endpoint to chat with the agent
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        # Panggil agent seperti pada websocket
        agent = call_agent(req.user_id, req.session_id)  # Samakan cara pemanggilan

        result = agent.run(req.message, show_full_reasoning=True)
        content = result.content

        if not isinstance(content, str):
            content = str(content)

        # Bersihkan log internal jika perlu
        cleaned_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\\n?", "", content)
        cleaned_response = re.sub(r" - Running:\s*\w+\(.*?\)\n?", "", cleaned_response)
        cleaned_response = re.sub(r" - Running:.*?\(.*?\)\n?", "", cleaned_response, flags=re.MULTILINE)

        return ChatResponse(reply=cleaned_response)
    except Exception as e:
        print(f"❌ Error saat memanggil agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
