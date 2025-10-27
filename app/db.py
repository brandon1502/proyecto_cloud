"""
Database initialization and session factory.

Este módulo crea el `engine` de SQLAlchemy usando `settings.DATABASE_URL` y expone
`SessionLocal` y la dependencia `get_db()` que las rutas usan con `Depends(get_db)`.

La variable `DATABASE_URL` debe tener un formato aceptado por SQLAlchemy + pymysql,
por ejemplo:

    mysql+pymysql://user:password@host:3306/database

En entornos Docker/Windows, `host.docker.internal` suele resolver al host Windows
desde el contenedor, lo que es útil cuando la BD corre en la máquina host.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.settings import settings


# Engine configurado desde la URL en settings (lee `.env` vía pydantic-settings)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

# Session factory usada por dependencias
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    """Generador de sesión para usar con FastAPI `Depends`.

    Uso:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
