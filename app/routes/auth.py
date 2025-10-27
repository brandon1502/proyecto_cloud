"""
Rutas de autenticación (registro/login/logout).

Descripción:
- POST /auth/register: registra un usuario desde formulario y redirige al login.
- POST /auth/login: autentica y emite JWT que se almacena en la tabla `api_tokens`.
  El JWT se envía como cookie HTTP-only.
- GET /auth/logout: borra la cookie y redirige al login.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db import get_db
from app.settings import settings
from app.services.users import create_user, authenticate_user, issue_session_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Registra un nuevo usuario y redirige al login."""
    _ = create_user(db, email=email, full_name=full_name, password=password)
    # Redirige al login con bandera de registro exitoso
    return RedirectResponse(url="/login?registered=1", status_code=303)


@router.post("/login")
def login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Valida credenciales, emite JWT y lo guarda en `api_tokens`.

    Devuelve una redirección a `/home` y escribe la cookie con el JWT.
    """
    user = authenticate_user(db, email, password)
    if not user:
        return RedirectResponse(url="/login?error=1", status_code=303)

    # emite JWT y guarda hash en api_tokens
    jwt_token = issue_session_token(db, user, client_ip=request.client.host)

    # Calcula max_age leyendo la exp del JWT (opcional). Si falla, dejamos cookie de sesión.
    try:
        from app.security import decode_jwt

        payload = decode_jwt(jwt_token)
        exp = payload.get("exp")
        max_age = int(exp - datetime.now(timezone.utc).timestamp()) if exp else None
    except Exception:
        max_age = None

    resp = RedirectResponse(url="/home", status_code=303)
    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=bool(int(settings.COOKIE_SECURE)),
        samesite=settings.COOKIE_SAMESITE,
        path="/",
        max_age=max_age if max_age and max_age > 0 else None,
    )
    return resp


@router.get("/logout")
def logout():
    """Borra la cookie del cliente y redirige al login."""
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(key=settings.COOKIE_NAME, path="/")
    return resp
