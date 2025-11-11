# app/deps.py
from fastapi import Cookie, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.models import User
from app.jwt_utils import verify_token


def login_required(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para rutas que requieren autenticación.
    Lee el JWT desde la cookie y retorna el usuario autenticado.
    """
    print(f"🔍 DEBUG login_required - access_token recibido: {repr(access_token)}")
    
    if not access_token:
        print("❌ DEBUG: No se recibió token en la cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado - token no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extraer token (viene como "Bearer <token>")
    token = access_token.replace("Bearer ", "").strip()
    print(f"🔍 DEBUG login_required - token extraído: {token[:50] if len(token) > 50 else token}...")
    
    # Verificar token y obtener user_id
    try:
        user_id = verify_token(token)
        print(f"✅ DEBUG: Token válido, user_id={user_id}")
    except Exception as e:
        print(f"❌ DEBUG: Error al verificar token: {e}")
        raise
    
    # Verificar token y obtener user_id
    user_id = verify_token(token)
    
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
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency para rutas que NO requieren autenticación pero pueden usar el usuario si está logueado.
    Retorna el usuario autenticado o None si no hay token válido.
    """
    if not access_token:
        return None
    
    try:
        # Extraer token (viene como "Bearer <token>")
        token = access_token.replace("Bearer ", "").strip()
        
        # Verificar token y obtener user_id
        user_id = verify_token(token)
        
        # Buscar usuario en BD
        user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
        
        return user
    except Exception:
        # Si hay cualquier error, simplemente retornamos None (no autenticado)
        return None
