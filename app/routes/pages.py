from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.deps import login_required, get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/registro", response_class=HTMLResponse)
def registro_page(request: Request, user = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse("registro.html", {"request": request})

@router.get("/home", response_class=HTMLResponse)
def home_page(request: Request, user = Depends(login_required)):
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@router.get("/plantillas", response_class=HTMLResponse)
def home_page(request: Request, user = Depends(login_required)):
    return templates.TemplateResponse("plantillas.html", {"request": request, "user": user})

@router.get("/plantillas/create", response_class=HTMLResponse)
def home_page(request: Request, user = Depends(login_required)):
    return templates.TemplateResponse("crear_plantilla.html", {"request": request, "user": user})


@router.get("/projects", response_class=HTMLResponse)
def home_page(request: Request, user = Depends(login_required)):
    return templates.TemplateResponse("proyectos.html", {"request": request, "user": user})