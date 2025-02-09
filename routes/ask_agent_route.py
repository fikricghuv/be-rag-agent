from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import time
import time 
from agents.product_information_agent.product_information_agent import call_agent
from config.config_db import config_db
from models.query_request_schema import QueryRequest
from models.chat_history_model import ChatHistory

router = APIRouter()

@router.post("/ask")
def ask_agent(request: QueryRequest, db: Session = Depends(config_db)):
    start_time = time.time()
    try:
        agent = call_agent(request.user_id, request.user_id)
        response = agent.run(request.question)
        save_response = response.content if isinstance(response.content, str) else str(response.content)
        latency = time.time() - start_time

        chat_history = ChatHistory(
            name=request.user_id,
            input=request.question,
            output=save_response,
            error=None,
            latency=latency,
            agent_name="product information agent",
        )
        db.add(chat_history)
        db.commit()
        return {"success": True, "data": save_response}
    except Exception as e:
        latency = time.time() - start_time
        chat_history = ChatHistory(
            name=request.user_id,
            input=request.question,
            output=None,
            error=str(e),
            latency=latency,
            agent_name="product information agent",
        )
        db.add(chat_history)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
