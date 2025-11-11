"""
Rutas de autenticación (registro/login/logout).

Descripción:
- POST /auth/register: registra un usuario desde formulario y redirige al login.
- POST /auth/login: autentica y emite JWT que se almacena como cookie HTTP-only.
- GET /auth/logout: borra la cookie y redirige al login.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import get_db
from app.services.users import create_user, authenticate_user
from app.jwt_utils import create_access_token


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
    return RedirectResponse(url="/login?registered=1", status_code=303)


@router.post("/login")
def login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Valida credenciales, emite JWT y lo guarda en cookie HTTP-only.
    Devuelve una redirección a `/home`.
    """
    user = authenticate_user(db, email, password)
    if not user:
        return RedirectResponse(url="/login?error=1", status_code=303)

    # Crear JWT token (sub debe ser string según estándar JWT)
    access_token = create_access_token(data={"sub": str(user.user_id)})
    print(f"🔐 DEBUG LOGIN: Token creado para user_id={user.user_id}, email={user.email}")
    print(f"🔐 DEBUG LOGIN: Token (primeros 50 chars): {access_token[:50]}...")

    # Actualizar last_login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Crear respuesta con redirección
    resp = RedirectResponse(url="/home", status_code=303)
    
    # Guardar JWT en cookie HTTP-only
    cookie_value = f"Bearer {access_token}"
    print(f"🍪 DEBUG LOGIN: Configurando cookie 'access_token'")
    print(f"🍪 DEBUG LOGIN: Cookie value: {cookie_value[:70]}...")
    
    resp.set_cookie(
        key="access_token",
        value=cookie_value,
        httponly=True,
        secure=False,  # True en producción con HTTPS
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24,  # 24 horas
    )
    
    print("✅ DEBUG LOGIN: Cookie configurada, redirigiendo a /home")
    return resp


@router.get("/logout")
def logout():
    """Borra la cookie del cliente y redirige al login."""
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(key="access_token", path="/")
    return resp
