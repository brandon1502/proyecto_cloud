# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "PUCP Orchestrator"

    # DB & auth
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    COOKIE_NAME: str = "orchestrator_session"
    COOKIE_SECURE: int = 0
    COOKIE_SAMESITE: str = "lax"

    # --- Despliegue externo (API de tu amigo) ---
    # URL de la API externa que recibirá el JSON guardado
    FRIEND_DEPLOY_API_URL: str | None = None
    # Token opcional (Authorization: Bearer <token>)
    FRIEND_DEPLOY_API_TOKEN: str | None = None
    # Timeout para httpx (segundos)
    HTTP_CLIENT_TIMEOUT: int = 30

    # .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
