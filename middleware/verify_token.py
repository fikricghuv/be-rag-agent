from fastapi import HTTPException, Request
import jwt
from config.settings import SECRET_KEY, ALGORITHM

# Middleware untuk memverifikasi JWT
def verify_token(request: Request):
    token = request.headers.get("Authorization")
    # print("get token: " + token)
    if not token:
        raise HTTPException(status_code=401, detail="Token missing.")
    
    # Pastikan token memiliki format "Bearer <token>"
    if not token.startswith("Bearer "):
        print("Invalid token format.")
        raise HTTPException(status_code=401, detail="Invalid token format.")
    
    try:
        token = token.split("Bearer ")[1]  # Ambil bagian token saja
        print("get clear token: " + token)
        decoded_token = jwt.decode(
            token,
            SECRET_KEY,  # Pastikan SECRET_KEY cocok
            algorithms=[ALGORITHM],  # Pastikan algoritma cocok
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        print("Token expired.")
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError as e:
        print("invalid token: " + str(e))
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e))