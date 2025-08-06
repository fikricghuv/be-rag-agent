# services/notification_service.py
import json
import logging
from sqlalchemy import or_, func, desc, update, and_
from database.models.notification_model import Notification
from redis.asyncio import Redis
from datetime import datetime
from uuid import UUID
from sqlalchemy.future import select
from core.config_db import get_db
from fastapi import Depends, HTTPException
from api.websocket.redis_client import get_redis_client
from sqlalchemy.ext.asyncio import AsyncSession

# Inisialisasi logger
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def create_notification(self, receiver_id: UUID | None, client_id: UUID, message: str, notif_type: str = "chat", is_broadcast: bool = False):
        logger.info(f"[NOTIF][CREATE] Creating notification - receiver_id={receiver_id}, type={notif_type}, broadcast={is_broadcast}")
        
        notif = Notification(
            receiver_id=receiver_id,
            message=message,
            type=notif_type,
            created_at=datetime.utcnow(),
            is_read=False,
            is_broadcast=is_broadcast,
            is_active=True,
            client_id=client_id 
        )

        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)

        channel = "notif:broadcast" if is_broadcast else f"notif:{receiver_id}"
        payload = {
            "id": str(notif.id),
            "message": message,
            "type": notif_type,
            "created_at": notif.created_at.isoformat()
        }

        logger.info(f"[NOTIF][PUBLISH] Publishing to channel: {channel} with payload: {payload}")
        await self.redis.publish(channel, json.dumps(payload))

    async def get_notifications(self, receiver_id: UUID, client_id: UUID, limit: int = 20, offset: int = 0):
        logger.info(f"[NOTIF][FETCH] Fetching notifications for user_id={receiver_id}, limit={limit}, offset={offset}")

        query = (
            select(Notification)
            .where(and_(Notification.receiver_id == receiver_id, Notification.is_active == True, Notification.client_id == client_id))
            .order_by(desc(Notification.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        count_query = select(func.count()).select_from(
            select(Notification).where(
                and_(Notification.receiver_id == receiver_id, Notification.is_active == True, Notification.client_id == client_id)
            ).subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        logger.info(f"[NOTIF][FETCH] Found {len(notifications)} notifications, total={total}")
        return notifications, total

    async def mark_notification_as_read(self, notification_id: UUID, receiver_id: UUID, client_id: UUID):
        logger.info(f"[NOTIF][UPDATE] Marking notification {notification_id} as read for user_id={receiver_id}")

        # Ambil notifikasi terlebih dahulu untuk validasi
        query = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.client_id == client_id
            )
        )
        result = await self.db.execute(query)
        notif = result.scalar_one_or_none()

        if not notif:
            logger.warning(f"[NOTIF][UPDATE] Notification {notification_id} not found")
            raise HTTPException(status_code=404, detail="Notification not found")

        if not notif.is_broadcast and notif.receiver_id != receiver_id:
            logger.warning(f"[NOTIF][UPDATE] User {receiver_id} unauthorized to update notification {notification_id}")
            raise HTTPException(status_code=403, detail="Unauthorized to update this notification")

        notif.is_read = True
        await self.db.commit()
        logger.info(f"[NOTIF][UPDATE] Notification {notification_id} marked as read")

        return {"status": "success", "notification_id": str(notification_id)}

    async def soft_delete_all_by_receiver(self, receiver_id: UUID, client_id: UUID):
        logger.info(f"[NOTIF][DELETE] Soft deleting all active notifications for receiver_id={receiver_id}")

        query = (
            update(Notification)
            .where(Notification.receiver_id == receiver_id)
            .where(Notification.is_active == True)
            .where(Notification.client_id == client_id)
            .values(is_active=False)
        )
        await self.db.execute(query)
        await self.db.commit()

        logger.info(f"[NOTIF][DELETE] All active notifications for receiver_id={receiver_id} marked as inactive")
        return {"status": "success", "receiver_id": str(receiver_id)}

def get_notification_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client)
) -> NotificationService:
    return NotificationService(db, redis)
