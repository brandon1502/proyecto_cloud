# app/deps.py
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.security import decode_jwt
from app.settings import settings

def get_current_user_optional(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_jwt(token)  # dict con sub/uid
    except Exception:
        return None

def login_required(request: Request, db: Session = Depends(get_db)):
    payload = get_current_user_optional(request)
    if not payload:
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login"})
    user_id = int(payload.get("uid") or payload.get("sub"))  # <- igual que arriba
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user  # <- ORM
