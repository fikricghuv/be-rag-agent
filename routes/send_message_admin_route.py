from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.chat_history_model import ChatHistory
from models.admin_message_request_schema import AdminMessageRequest

router = APIRouter()

@router.post("/send-admin-message")
def send_admin_message(request: AdminMessageRequest, db: Session = Depends(config_db)):
    
    try:
        # Simpan pesan admin sebagai pesan dari bot
        chat_history = ChatHistory(
            name=request.user_id,
            input="",  
            output=request.message,
            error=None,
            latency=0,  
            agent_name="admin",  
        )
        db.add(chat_history)
        db.commit()

        return {
            "success": True,
            "data": {
                "user_id": request.user_id,
                "message": request.message,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
