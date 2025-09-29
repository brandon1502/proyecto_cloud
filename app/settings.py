# app/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "PUCP Private Orchestrator"
    JWT_SECRET: str = Field(default="devsupersecret-change-me")  # cámbialo en prod
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 8 * 60  # 8 horas
    COOKIE_NAME: str = "access_token"
    COOKIE_SAMESITE: str = "lax"
    COOKIE_SECURE: bool = False  # en prod: True (HTTPS)
    DEBUG: bool = True

settings = Settings()
