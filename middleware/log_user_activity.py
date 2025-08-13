
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import Message
from sqlalchemy.orm import Session
from core.config_db import config_db
from database.models.user_activity_log_model import UserActivityLog
import uuid
import datetime
import jwt
from core.settings import ALGORITHM, SECRET_KEY_ADMIN
import json

async def log_user_activity(request: Request, call_next: RequestResponseEndpoint) -> Response:
    print("proses User activity logged.")

    request_body = await request.body()
    request_body_str = None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            request_body_str = request_body.decode("utf-8")
        except UnicodeDecodeError:
            request_body_str = None

    auth_header = request.headers.get("authorization")
    user_id = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
            raw_user_id = payload.get("user_id") or payload.get("sub")
            user_id = uuid.UUID(raw_user_id) if raw_user_id else None
        except Exception as e:
            print("JWT decode error:", str(e))

    response: Response = await call_next(request)

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    new_response = Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )

    try:
        db: Session = next(config_db())

        request_json = None
        try:
            request_json = json.loads(request_body_str) if request_body_str else None
        except Exception:
            request_json = None  

        response_json = None
        try:
            response_json = json.loads(response_body.decode("utf-8")) if response_body else None
        except Exception:
            response_json = None
            
        client_id = getattr(request.state, "client_id", None)

        if not client_id:
            print("⚠️ Skip logging: client_id is missing")
            return new_response

        log = UserActivityLog(
            user_id=user_id,
            client_id=client_id,
            endpoint=str(request.url.path),
            method=request.method,
            request_data=request_json,
            response_data=response_json,
            status_code=new_response.status_code,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log)
        db.commit()
        print("✅ User activity logged.")
    except Exception as e:
        print("❌ Logging failed:", str(e))

    return new_response
