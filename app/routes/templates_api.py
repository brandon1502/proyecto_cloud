from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import login_required
from app.models import Template

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("")
def list_templates(db: Session = Depends(get_db), user = Depends(login_required)):
    q = select(Template).where(Template.owner_id == int(user["sub"]))
    rows = db.scalars(q).all()
    return [{"template_id": t.template_id, "name": t.name, "status": t.status} for t in rows]

@router.post("")
def create_template(
    name: str = Form(...),
    placement_strategy: str = Form(None),
    internet_egress: int = Form(0),
    db: Session = Depends(get_db),
    user = Depends(login_required)
):
    t = Template(
        owner_id=int(user["sub"]),
        name=name,
        placement_strategy=placement_strategy,
        internet_egress=bool(internet_egress),
        created_by=int(user["sub"])
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"ok": True, "template_id": t.template_id}
