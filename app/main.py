# app/main.py
"""FastAPI application entrypoint.

Instancia la aplicación, monta archivos estáticos y registra routers.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.settings import settings
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.routes import slices_api
from app.routes import flavours
from app.routes.templates import router as templates_router
from app.routes import deployments

# App principal
app = FastAPI(title=settings.APP_NAME)

# Montar archivos estáticos (CSS, JS, imágenes). Las plantillas usan /static/...
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Registrar routers (rutas agrupadas por módulos)
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(slices_api.router)
app.include_router(templates_router)
app.include_router(flavours.router)
app.include_router(deployments.router)


@app.get("/healthz")
def healthz():
    """Endpoint de salud simple usado por orquestadores o para debugging."""
    return {"ok": True}
