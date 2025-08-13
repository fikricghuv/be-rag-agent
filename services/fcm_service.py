import json
import time
from jose import jwt
import httpx
from uuid import UUID
from core.settings import FIREBASE_CONFIG
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user_model import User, UserFCM
from firebase_admin import messaging
from exceptions.custom_exceptions import DatabaseException

SCOPES = "https://www.googleapis.com/auth/firebase.messaging"

class FCMService:
    def __init__(self, db: AsyncSession):
        self._load_credentials()

    def _load_credentials(self):
        if not FIREBASE_CONFIG:
            raise ValueError("FIREBASE_CONFIG environment variable is not set")

        try:
            creds = json.loads(FIREBASE_CONFIG)
            self.project_id = creds["project_id"]
            self.private_key = creds["private_key"]
            self.client_email = creds["client_email"]
        except Exception as e:
            raise ValueError(f"Gagal parsing FIREBASE_CONFIG: {e}")

    def _generate_access_token(self):
        now = int(time.time())
        payload = {
            "iss": self.client_email,
            "sub": self.client_email,
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": now + 3600,
            "scope": SCOPES
        }

        jwt_token = jwt.encode(payload, self.private_key, algorithm="RS256")

        response = httpx.post("https://oauth2.googleapis.com/token", data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token
        })

        response.raise_for_status()
        return response.json()["access_token"]
    
    async def save_fcm_token(self, db: AsyncSession, user_id: UUID, token: str, client_id: UUID) -> None:
        try:
            if isinstance(user_id, User): 
                user_id = user_id.id

            existing = await db.execute(
                select(UserFCM).where(UserFCM.user_id == user_id, UserFCM.token == token)
            )
            fcm_record = existing.scalar_one_or_none()

            if not fcm_record:
                new_token = UserFCM(user_id=user_id, token=token, client_id=client_id)
                db.add(new_token)
                await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseException(code="SAVE_TOKEN_FCM", message="Failed to save token fcm.")


    async def send_message(self, fcm_token: str, title: str, body: str):
        access_token = self._generate_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "message": {
                "token": fcm_token,
                "notification": {
                    "title": title,
                    "body": body
                }
            }
        }

        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            return res.json()
        