# app/services/chat_service.py
from sqlalchemy.orm import Session
from agents.customer_service_agent.customer_service_agent import call_customer_service_agent
from controllers.auth_controller import AuthController
from fastapi import WebSocket, Depends
import asyncio
import time
import re
from database.models.chat_history_model import ChatHistory, ChatHistoryEmbedding
from agno.embedder.openai import OpenAIEmbedder
import numpy as np
from core.config_db import config_db

embedder = OpenAIEmbedder()

class ChatService:
    def __init__(self, db: Session, active_connections: dict = None, active_agents: dict = None):
        self.db = db
        self.active_connections = active_connections
        self.active_agents = active_agents
        self._connections_lock = asyncio.Lock()
        self._agents_lock = asyncio.Lock()

    async def validate_initial_connection(self, websocket: WebSocket, chatId: str, role: str):
        if not chatId or role not in ["user", "admin"]:
            await websocket.send_json({"error": "chatId dan/atau role tidak valid"})
            await websocket.close(code=1008)
            return False
        verify_id = AuthController().get_chat_id_data(chatId, self.db)
        if not verify_id:
            await websocket.send_json({"error": "chatId tidak ditemukan di database"})
            await websocket.close(code=1008)
            return False
        return True

    def save_chat_history(self, db: Session, user_id: str, question: str, save_response: str, latency: float):
        save_response = re.sub(r" - Running:.*?\n?", "", save_response, flags=re.MULTILINE)
        print(f"DEBUG: Nilai db sebelum commit: {db}")
        chat_history = ChatHistory(
            name=user_id,
            input=question,
            output=save_response,
            error=None,
            latency=latency,
            agent_name="Customer Service Agent",
        )
        db.add(chat_history)
        try:
            db.commit()
        except Exception as e:
            print(f"Error saat commit: {e}")
            db.rollback() # Penting untuk rollback jika terjadi error
            raise  # Await commit untuk async session

        chat_history_id = chat_history.id

        embedding_question = embedder.get_embedding(question)
        embedding_answer = embedder.get_embedding(save_response)
        embedding_question_array = np.array(embedding_question).tolist()
        embedding_answer_array = np.array(embedding_answer).tolist()

        chat_history_embedding = ChatHistoryEmbedding(
            refidchathistory=chat_history_id,
            embedding_answer=embedding_answer_array,
            embedding_question=embedding_question_array
        )

        db.add(chat_history_embedding)
        db.commit()  # Await commit untuk async session
        return save_response

    async def handle_user_message(self, websocket: WebSocket, data: dict, chatId: str, start_time: float):
        question = data.get("question")
        if not question:
            await websocket.send_json({"success": False, "error": "Pesan diperlukan"})
            return
        try:
            agent = call_customer_service_agent(chatId, chatId)
            print("🧠 Memanggil agent...")

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, agent.run, question)
            latency = round(time.time() - start_time, 2)

            print("response :" , response.content)
            save_response = self.save_chat_history(self.db, chatId, question, response.content, latency)
            print("succes save response")
            await websocket.send_json({"success": True, "data": save_response})
            await self._broadcast_to_admins(chatId, question, save_response)
        except Exception as e:
            print(f"Error handling user message: {e}")
            await websocket.send_json({"success": False, "error": f"Terjadi kesalahan: {e}"})

    async def _broadcast_to_admins(self, user_id: str, question: str, output: str):
        active_users_copy = self.active_connections.copy()
        for admin_id, conn in active_users_copy.items():
            if conn["role"] == "admin":
                try:
                    await conn["websocket"].send_json({
                        "success": True,
                        "user_id": user_id,
                        "question": question,
                        "output": output
                    })
                    print(f"📨 Pesan dikirim ke admin {admin_id}")
                except Exception as e:
                    print(f"❌ Gagal mengirim pesan ke admin {admin_id}: {e}")

    async def handle_admin_message(self, websocket: WebSocket, data: dict, chatId: str, start_time: float):
        target_user_id = data.get("user_id")
        admin_message = data.get("question")
        if not target_user_id or not admin_message:
            await websocket.send_json({"success": False, "error": "Target user dan pesan diperlukan"})
            return
        target_conn = self.active_connections.get(target_user_id)
        if target_conn and target_conn["role"] == "user":
            latency = round(time.time() - start_time, 2)
            self.save_chat_history(self.db, target_user_id, '', admin_message, latency)
            await target_conn["websocket"].send_json({"success": True, "data": admin_message, "from": "admin"})
            await websocket.send_json({"success": True, "admin_message": admin_message, "user_id": target_user_id})
        else:
            await websocket.send_json({"success": False, "error": "User tidak ditemukan atau tidak aktif"})

    async def handle_disconnect(self, chatId: str, role: str):
        print(f"{role.capitalize()} {chatId} terputus")
        if chatId in self.active_connections:
            self.active_connections.pop(chatId)
        if chatId in self.active_agents:
            self.active_agents.pop(chatId)
        await asyncio.sleep(0.1)
        await self._broadcast_active_users()

    async def _broadcast_active_users(self):
        active_users_copy = self.active_connections.copy()
        for conn in active_users_copy.values():
            try:
                await conn["websocket"].send_json({"type": "active_users", "users": list(active_users_copy.keys())})
            except Exception as e:
                print(f"❌ Gagal mengirim daftar pengguna aktif: {e}")

    async def process_chat_message(self, user_id: str, session_id: str, message: str) -> str:
        try:
            agent = call_customer_service_agent(user_id, session_id)
            result = agent.run(message, show_full_reasoning=True)
            content = result.content

            if not isinstance(content, str):
                content = str(content)

            cleaned_response = re.sub(r" - Running:\s*search_knowledge_base\(query=.*?\)\\n?", "", content)
            cleaned_response = re.sub(r" - Running:\s*\w+\(.*?\)\n?", "", cleaned_response)
            cleaned_response = re.sub(r" - Running:.*?\(.*?\)\n?", "", cleaned_response, flags=re.MULTILINE)

            return cleaned_response
        except Exception as e:
            print(f"❌ Error saat memanggil agent di service: {e}")
            raise

def get_chat_service(db: Session = Depends(config_db)):
    return ChatService(db)