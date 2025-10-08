# app/deps.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.settings import settings
from app.security import decode_jwt

def get_current_user_optional(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_jwt(token)  # {"sub": "...", "role": "...", "exp": ...}
        return payload
    except Exception:
        return None

def login_required(request: Request):
    user = get_current_user_optional(request)
    if not user:
        # opción A: redirigir a /login (recomendado para páginas HTML)
        # Nota: en una dependencia no puedes retornar una Response directamente,
        # pero puedes lanzar una HTTPException con 307 y el middleware/cliente hará la redirección.
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login"})
        # opción B: si prefieres JSON 401
        # raise HTTPException(status_code=401, detail="No autenticado")
    return user
