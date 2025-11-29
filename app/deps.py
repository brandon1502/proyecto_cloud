# app/deps.py
from fastapi import Cookie, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.models import User
from app.jwt_utils import verify_token


def login_required(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para rutas que requieren autenticación.
    Lee el JWT desde la cookie O desde el header Authorization.
    Retorna el usuario autenticado.
    """
    token = None
    
    # Prioridad 1: Cookie (para navegadores)
    if access_token:
        token = access_token.replace("Bearer ", "").strip()
        print(f"🔍 DEBUG: Token desde cookie: {token[:50] if len(token) > 50 else token}...")
    
    # Prioridad 2: Header Authorization (para Postman/APIs)
    elif authorization:
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "").strip()
            print(f"🔍 DEBUG: Token desde header Authorization: {token[:50] if len(token) > 50 else token}...")
        else:
            print("❌ DEBUG: Header Authorization no tiene formato 'Bearer <token>'")
    
    # Sin token en ninguno de los dos lugares
    if not token:
        print("❌ DEBUG: No se recibió token (ni en cookie ni en header)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado - token no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar token y obtener user_id
    try:
        user_id = verify_token(token)
        print(f"✅ DEBUG: Token válido, user_id={user_id}")
    except Exception as e:
        print(f"❌ DEBUG: Error al verificar token: {e}")
        raise
    
    # Buscar usuario en BD
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    
    return user


def get_current_user_optional(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency para rutas que NO requieren autenticación pero pueden usar el usuario si está logueado.
    Retorna el usuario autenticado o None si no hay token válido.
    """
    token = None
    
    # Desde cookie (navegadores)
    if access_token:
        token = access_token.replace("Bearer ", "").strip()
    # Desde header Authorization (Postman/APIs)
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
    
    if not token:
        return None
    
    try:
        # Verificar token y obtener user_id
        user_id = verify_token(token)
        
        # Buscar usuario en BD
        user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
        
        return user
    except Exception:
        # Si hay cualquier error, simplemente retornamos None (no autenticado)
        return None
