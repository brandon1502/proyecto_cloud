# app/main.py
"""FastAPI application entrypoint.

Instancia la aplicación, monta archivos estáticos y registra routers.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from app.settings import settings

from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.routes.slices_api import router as slices_router
from app.routes.flavours import router as flavours_router
from app.routes.templates import router as templates_router
from app.routes.deployments import router as deployments_router
from app.routes.vnc_proxy import router as vnc_proxy_router
from app.routes.vnc_websocket import router as vnc_websocket_router

# App principal
app = FastAPI(title=settings.APP_NAME)

# Montar archivos estáticos (CSS, JS, imágenes). Las plantillas usan /static/...
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Registrar routers (rutas agrupadas por módulos)
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(slices_router)
app.include_router(flavours_router)
app.include_router(templates_router)
app.include_router(deployments_router)
app.include_router(vnc_proxy_router)
app.include_router(vnc_websocket_router)


@app.get("/healthz")
def healthz():
    """Endpoint de salud simple usado por orquestadores o para debugging."""
    return {"ok": True}


# Handler global para HTTPException: si es 401 y el cliente acepta HTML, redirigimos al login.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Intercepta excepciones HTTP lanzadas por dependencias (p.ej. login_required).

    - Si el status es 401 y el cliente es un navegador (acepta text/html) redirige a /login.
    - En otros casos devuelve la respuesta JSON por defecto.
    """
    try:
        accept = request.headers.get("accept", "")
        # Detectar si cliente prefiere HTML
        wants_html = "text/html" in accept or "application/xhtml+xml" in accept

        if exc.status_code == status.HTTP_401_UNAUTHORIZED and wants_html:
            # Redirigir al login para UX en navegadores
            return RedirectResponse(url="/login")

        # Por defecto, devolver JSON con el detalle del error
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception:
        # Fallback: devolver JSON simple
        return JSONResponse(status_code=500, content={"detail": "Internal server error in exception handler"})
