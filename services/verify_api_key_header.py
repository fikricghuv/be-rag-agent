# Import untuk keamanan API Key
from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Depends, status
from core.settings import VALID_API_KEYS
# --- Keamanan: Contoh Dependency untuk API Key Authentication ---
# Anda perlu menyimpan API_KEY_SECRET ini di environment variable atau secret management system,
# JANGAN HARDCODE DI SINI dalam aplikasi produksi.
# Mengambil secret dari environment variable, dengan fallback nilai default (untuk development)


# Mendefinisikan skema keamanan API Key di header 'X-API-Key'
api_key_header = APIKeyHeader(name="X-API-Key")

def api_key_auth(api_key: str = Depends(api_key_header)):
    """
    Dependency untuk memvalidasi API Key dari header 'X-API-Key'.
    """
    if api_key != VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    # Mengembalikan API Key yang valid (bisa juga mengembalikan objek user terkait jika ada)
    return api_key