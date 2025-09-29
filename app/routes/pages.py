# app/routes/pages.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.deps import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _require_user(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return None
    return user

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = get_current_user_optional(request)
    # Si ya tiene token válido, muéstrale la primera vista (/home)
    if user:
        return RedirectResponse("/home", status_code=303)
    return RedirectResponse("/login", status_code=303)

@router.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    # Renderiza TU nueva primera interfaz
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@router.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("proyectos.html", {"request": request, "user": user})

# ✅ Nueva ruta: Crear topología
@router.get("/projects/create", response_class=HTMLResponse)
def create_topology_page(request: Request):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("crear_topologia.html", {"request": request, "user": user})

@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail_page(project_id: str, request: Request):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        "ver_proyecto.html", {"request": request, "user": user, "project_id": project_id}
    )

@router.get("/api/topology")
def get_topology(request: Request):
    user = _require_user(request)
    if not user:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return {
        "nodes": [
            {"id": "server1", "label": "server1", "shape": "box"},
            {"id": "server2", "label": "server2", "shape": "box"},
            {"id": "ofs",     "label": "OFS",     "shape": "ellipse"},
            {"id": "gw",      "label": "Gateway", "shape": "diamond"},
        ],
        "edges": [
            {"from": "server1", "to": "ofs"},
            {"from": "server2", "to": "ofs"},
            {"from": "ofs",     "to": "gw"},
        ]
    }

@router.get("/api/me")
def me(request: Request):
    user = _require_user(request)
    if not user:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return {"sub": user["sub"], "role": user["role"]}
