# app/services/users.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import User, ApiToken
from app.security import (
    verify_password,
    hash_password,
    make_jwt,
    decode_jwt,
    sha256_hex,
)
from app.settings import settings

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))

def create_user(db: Session, email: str, full_name: str, password: str) -> User:
    # valida duplicado a nivel app (además del UNIQUE)
    if get_user_by_email(db, email):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="email already registered")

    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        is_active=True,
        created_at=datetime.now(timezone.utc),
        role_id=2,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



def authenticate_user(db: Session, email: str, password: str) -> User | None:
    u = get_user_by_email(db, email)
    if not u or not u.is_active:
        return None
    if not verify_password(password, u.password_hash):
        return None
    return u

def issue_session_token(db: Session, user: User, client_ip: str | None = None) -> str:
    # 1) genera JWT (string)
    jwt_token = make_jwt(sub=str(user.user_id), role="user")

    # 2) lee exp del JWT
    payload = decode_jwt(jwt_token)
    exp_ts = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None

    # 3) guarda hash en api_tokens
    token_hash = sha256_hex(jwt_token)
    api_row = ApiToken(
        user_id=user.user_id,
        token_type="session",
        token_hash=token_hash,
        scopes=None,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at or datetime.now(timezone.utc),
        last_used_at=None,
        inactive_timeout_sec=None,
        revoked=False,
        created_by_ip=client_ip,
    )
    db.add(api_row)

    # (opcional) marca último login
    user.last_login_at = datetime.now(timezone.utc)

    db.commit()
    return jwt_token
