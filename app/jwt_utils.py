"""Utilidades para manejo de JWT tokens."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

# Configuración JWT
SECRET_KEY = "yEP4dsRJFHyHUky9C1Kr-KkKsFlyxgLUqhS3YOzYRzdKxvfQRB4-mZQ1YivNS5KiGs-QEWTgK-D_ZTfbJBwazg"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT token.
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": user_id})
        expires_delta: Tiempo de expiración personalizado
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> int:
    """
    Verifica y decodifica un JWT token.
    
    Args:
        token: Token JWT a verificar
    
    Returns:
        user_id del token
    
    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta el subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convertir de string a int
        return int(user_id_str)
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
