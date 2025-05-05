# -*- coding: utf-8 -*-
import uuid
from models.chat_ids_model import ChatIds, UserRole
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from config.config_db import config_db
import datetime

class AuthController:
    def generate_chat_id(self, role: str, db: Session = Depends(config_db)):
        """
        Menghasilkan dan menyimpan chat_id berdasarkan role (user atau admin).

        Args:
            role: Peran untuk chat_id ('user' atau 'admin').
            db: Sesi database SQLAlchemy.

        Returns:
            str: Chat ID yang dihasilkan.

        Raises:
            HTTPException: Jika peran tidak valid.
        """

        if role.lower() == 'user':
            db_role = UserRole.user #Perbaikan
            print(f"🔑 db_role sebelum ChatIds: {db_role}, value: {db_role.value}")
        elif role.lower() == 'admin':
            db_role = UserRole.admin #Perbaikan
        else:
             raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'.")

        chat_id = str(uuid.uuid4())

        db_chat_id = ChatIds(chat_id=chat_id, role=db_role, created_at=func.now())  # Gunakan model UserAdminIDs
        db.add(db_chat_id)
        db.commit()
        db.refresh(db_chat_id)

        return chat_id

    def get_chat_id_data(self, chat_id: str, db: Session):
        """
        Mendapatkan data chat berdasarkan chat_id.

        Args:
            chat_id: ID chat yang akan dicari.
            db: Sesi database SQLAlchemy.

        Returns:
            dict: Data chat jika ditemukan, None jika tidak.
        """
        chat_data = db.query(ChatIds).filter(ChatIds.chat_id == chat_id).first()  # Gunakan UserAdminIDs
        if chat_data:
            return {
                "chat_id": chat_data.chat_id,
                "role": chat_data.role,
                "created_at": chat_data.created_at,
            }
        return None