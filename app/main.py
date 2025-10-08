from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.settings import settings
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router

app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(pages_router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
