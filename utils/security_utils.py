from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
# Inisialisasi context bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Menghasilkan hash dari password plain text menggunakan bcrypt.

    Args:
        password (str): Password plain text.

    Returns:
        str: Password yang sudah di-hash.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Memverifikasi password plain text terhadap hash-nya.

    Args:
        plain_password (str): Password asli yang dimasukkan user.
        hashed_password (str): Hash password yang tersimpan.

    Returns:
        bool: True jika cocok, False jika tidak.
    """
    logger.warning(f"[SERVICE][AUTH] Verify pass: {plain_password} and {hashed_password}")
    return pwd_context.verify(plain_password, hashed_password)
