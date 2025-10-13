# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FRIEND_DEPLOY_API_URL: str = "http://localhost:1234/api/deploy"  # <-- cámbialo
    FRIEND_DEPLOY_API_TOKEN: str | None = None  # opcional
    HTTP_CLIENT_TIMEOUT: int = 30

settings = Settings()
