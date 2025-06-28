from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from api.endpoints.auth_endpoint import router as auth_endpoint
from api.endpoints.chat_history_endpoint import router as chat_history_endpoint
from api.endpoints.customer_feedback_endpoint import router as customer_feedback_endpoint
from api.endpoints.dashboard_endpoint import router as dashboard_endpoint
from api.endpoints.files_endpoint import router as files_endpoint
from api.endpoints.knowledge_base_endpoint import router as knowledge_base_endpoint
from api.endpoints.prompt_endpoint import router as prompt_endpoint
from api.endpoints.room_endpoint import router as room_endpoint
from api.websocket.chat_ws import router as chat_ws

from fastapi.staticfiles import StaticFiles 

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

app.state.active_websockets = {}

app.state.admin_room_associations = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    # allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):

    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"

    return response

@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded."},
    )

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

# app.mount("/static", StaticFiles(directory="/Users/cghuv/Documents/Project/AGENT-PROD/app/resources/uploaded_files"), name="static_files")
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Path relatif terhadap folder kerja container (/app)
static_path = Path("resources/uploaded_files")
static_path.mkdir(parents=True, exist_ok=True)  

app.mount("/static", StaticFiles(directory=static_path), name="static_files")

@app.get("/")
@limiter.limit("10/minute")  
async def read_root(request: Request): 
    return {"message": "Welcome to the Service Monitoring TalkVera!"}
