from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.settings import settings

app = FastAPI(title=settings.APP_NAME)

# /static para imágenes/css/js propios (si usas)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(pages_router)

# Healthcheck simple
@app.get("/healthz")
def healthz():
    return {"ok": True}
