from fastapi import Request
from app.settings import settings
from app.security import decode_jwt

def get_current_user_optional(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_jwt(token)
        # payload esperado: {"sub": "<user_id>", "role": "...", "exp": ...}
        return payload
    except Exception:
        return None
