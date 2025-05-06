from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func, text, desc
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from typing import List
from database.models.chat_history_model import ChatHistory

class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_total_unique_users(self) -> int:
        try:
            total_user = self.db.query(func.count(func.distinct(ChatHistory.name))).scalar()
            return total_user
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Database error: " + str(e))

    def fetch_unique_names_from_history(self) -> List[dict]:
        query = (
            select(
                text("name"),
                func.max(text("start_time")).label("last_update")
            )
            .select_from(text("ai.chat_history"))
            .group_by(text("name"))
            .order_by(func.max(text("start_time")).desc())
        )
        result = self.db.execute(query)
        return [{"name": row[0], "last_update": row[1]} for row in result.fetchall()]

    def fetch_chat_history(self) -> List[ChatHistory]:
        """Mengambil seluruh riwayat chat dari database, diurutkan berdasarkan waktu mulai (start_time) terbaru."""
        return self.db.execute(
            select(ChatHistory).order_by(desc(ChatHistory.start_time))
        ).scalars().all()

    def fetch_chat_history_by_user(self, user_name: str) -> List[ChatHistory]:
        """Mengambil riwayat chat berdasarkan nama pengguna."""
        result = self.db.execute(
            select(ChatHistory).where(ChatHistory.name == user_name)
        ).scalars().all()
        return result
    
    def get_total_conversations(self) -> int:
        """
        Mengambil total jumlah baris (total percakapan) dari tabel ChatHistory.
        """
        try:
            total_conversations = self.db.query(func.count()).select_from(ChatHistory).scalar()
            return total_conversations
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Database error: " + str(e))