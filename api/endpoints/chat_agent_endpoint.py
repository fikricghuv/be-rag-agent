from fastapi import APIRouter, HTTPException, Depends
from agents.customer_service_team.customer_service_team import call_agent
from models.chat_model import ChatRequest, ChatResponse
from services.chat_service import ChatService, get_chat_service

router = APIRouter()

# Endpoint to chat with the agent
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    try:
        reply = await chat_service.process_chat_message(req.user_id, req.session_id, req.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        print(f"❌ Error di endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))