# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "PUCP Orchestrator"
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    COOKIE_NAME: str = "orchestrator_session"
    COOKIE_SECURE: int = 0
    COOKIE_SAMESITE: str = "lax"

    # Configuración para leer .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
