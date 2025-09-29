from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.users import verify_user
from app.security import make_jwt
from app.settings import settings
from app.deps import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

# app/routes/auth.py
@router.post("/auth/login")
def auth_login(username: str = Form(...), password: str = Form(...)):
    user = verify_user(username, password)
    if not user:
        return RedirectResponse("/login?error=1", status_code=303)

    token = make_jwt(sub=user.id, role=user.role)
    resp = RedirectResponse("/home", status_code=303)  # <- antes era /dashboard
    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )
    return resp


@router.get("/auth/logout")
def auth_logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(settings.COOKIE_NAME, path="/")
    return resp
