from fastapi import APIRouter, HTTPException
import jwt
from datetime import datetime, timedelta
from config.settings import SECRET_KEY_ADMIN, ALGORITHM, SECRET_KEY_REFRESH_ADMIN
from models.generate_token_request_schema import AdminTokenRequest, AdminRefreshTokenRequest

router = APIRouter()

# Penyimpanan sementara refresh token
refresh_tokens = {}

# Helper Function
def create_access_token(admin_id: str, role: str = "admin", expires_delta: timedelta = timedelta(minutes=15)) -> str:
    to_encode = {
        "sub": admin_id,
        "role": role,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY_ADMIN, algorithm=ALGORITHM)

def create_refresh_token(admin_id: str, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = {
        "sub": admin_id,
        "type": "refresh",
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY_REFRESH_ADMIN, algorithm=ALGORITHM)

# Generate Access + Refresh Token untuk Admin
@router.post("/auth/generate-admin-token")
def generate_token(request: AdminTokenRequest):
    access_token = create_access_token(request.admin_id)
    refresh_token = create_refresh_token(request.admin_id)

    # Simpan sementara (optional, bisa ganti pakai DB)
    refresh_tokens[refresh_token] = request.admin_id

    return {"token": access_token, "refresh_token": refresh_token}

# Refresh Access Token Admin
@router.post("/auth/refresh-admin-token")
def refresh_token_admin(request: AdminRefreshTokenRequest):
    try:
        decoded = jwt.decode(request.refresh_token_admin, SECRET_KEY_REFRESH_ADMIN, algorithms=[ALGORITHM])
        admin_id = decoded.get("sub")
        token_type = decoded.get("type")

        if token_type != "refresh" or not admin_id:
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        # Validasi token tersimpan (opsional)
        if request.refresh_token_admin not in refresh_tokens or refresh_tokens[request.refresh_token_admin] != admin_id:
            raise HTTPException(status_code=401, detail="Refresh token not recognized")

        new_access_token = create_access_token(admin_id)
        return {"token": new_access_token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
