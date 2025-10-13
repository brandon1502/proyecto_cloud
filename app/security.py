# app/security.py
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import os
import jwt
from passlib.context import CryptContext
from app.settings import settings

# Hash de contraseñas sin dolores de cabeza con bcrypt
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def make_jwt(sub: str, role: str = "user", uid: int | None = None):
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": sub, "role": role, "exp": exp}
    if uid is not None:
        payload["uid"] = uid
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_jwt(token: str):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

# ========= helpers que usa services/users.py =========

def sha256_hex(data: str) -> str:
    """Devuelve el SHA-256 en hex de un string (UTF-8)."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def new_token_string(nbytes: int = 32) -> str:
    """Token aleatorio URL-safe (p. ej. para tokens de consola/pat)."""
    return base64.urlsafe_b64encode(os.urandom(nbytes)).rstrip(b"=").decode("ascii")
