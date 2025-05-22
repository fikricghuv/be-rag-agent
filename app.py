from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.endpoints.files_endpoint import router as files_endpoint
from api.endpoints.customer_feedback_endpoint import router as customer_feedback_endpoint
from api.endpoints.knowledge_base_endpoint import router as knowledge_base_endpoint
from api.endpoints.chat_history_endpoint import router as chat_history_endpoint
from api.endpoints.auth_endpoint import router as auth_endpoint
from api.endpoints.room_endpoint import router as room_endpoint
from api.endpoints.dashboard_endpoint import router as dashboard_endpoint
from api.endpoints.prompt_endpoint import router as prompt_endpoint
from api.websocket.chat_ws import router as chat_ws
from starlette.responses import JSONResponse


# Inisialisasi aplikasi dan limiter
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# Inisialisasi state untuk menyimpan websockets aktif
# Dict[UUID, WebSocket] -> user_id (UUID) -> websocket object
app.state.active_websockets = {}

# Inisialisasi state baru untuk menyimpan admin_user_id -> room_id yang sedang dilihat
# Dict[UUID, UUID] -> admin_user_id (UUID) -> room_id (UUID)
app.state.admin_room_associations = {}

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:4200", "http://localhost:52266"],
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):

    response = await call_next(request)
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    # response.headers["X-Content-Type-Options"] = "nosniff"
    # response.headers["X-Frame-Options"] = "DENY"
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # response.headers["Referrer-Policy"] = "no-referrer"

    return response


# Tambahkan handler untuk rate limit error
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded."},
    )

# Tambahkan handler untuk API Key error
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 403:
        print("Forbidden: Invalid or missing API Key.")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Forbidden: Invalid or missing API Key."},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Daftarkan route Endpoint
app.include_router(files_endpoint)
app.include_router(customer_feedback_endpoint)
app.include_router(knowledge_base_endpoint)
app.include_router(chat_history_endpoint)
app.include_router(auth_endpoint)
app.include_router(room_endpoint)
app.include_router(dashboard_endpoint)
app.include_router(prompt_endpoint)

#Daftar route websocket
app.include_router(chat_ws)


# Rate limit untuk root endpoint
@app.get("/")
@limiter.limit("10/minute")  # Maksimum 10 request per menit
async def read_root(request: Request):  # Tambahkan parameter 'request'
    return {"message": "Welcome to the Service Monitoring Agent!"}
