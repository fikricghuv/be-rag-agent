# app/api/websocket/agent_websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from core.config_db import config_db
from services.chat_service import ChatService
import time

router = APIRouter()
active_connections = {}
active_agents = {}

async def broadcast_active_users():
    active_users_copy = active_connections.copy()
    for conn in active_users_copy.values():
        try:
            await conn["websocket"].send_json({"type": "active_users", "users": list(active_users_copy.keys())})
        except Exception as e:
            print(f"❌ Gagal mengirim daftar pengguna aktif: {e}")

@router.get("/active-users")
async def get_active_users():
    active_users = [{"user_id": chatId, "role": conn["role"]} for chatId, conn in active_connections.items()]
    return {"success": True, "active_users": active_users}

@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, chatId: str = None, role: str = None, db: Session = Depends(config_db)):
    global start_time
    start_time = time.time()
    chat_service = ChatService(db, active_connections, active_agents) # Pass state

    print("🔑 Token diterima:", chatId, role)

    if not await chat_service.validate_initial_connection(websocket, chatId, role):
        return

    try:
        await websocket.accept()
        active_connections[chatId] = {"websocket": websocket, "role": role}
        await broadcast_active_users()

        try:
            while True:
                data = await websocket.receive_json()
                print("📩 Data diterima:", data)
                received_role = data.get("role")
                received_chatId = data.get("user_id")

                if received_role == "user":
                    await chat_service.handle_user_message(websocket, data, received_chatId, start_time)
                elif received_role == "admin":
                    await chat_service.handle_admin_message(websocket, data, received_chatId, start_time)

        except WebSocketDisconnect:
            await chat_service.handle_disconnect(chatId, role)

    finally:
        await chat_service.handle_disconnect(chatId, role)