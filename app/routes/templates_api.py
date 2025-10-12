"""
templates_api.py
=================
Gestión de plantillas (templates) de slices.
Cumple con los requerimientos R1B y R1C:
- Permite listar y crear plantillas desde la interfaz web.
- Cada template representa una topología de slice diseñada por el usuario.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import login_required
from app.models import Template
from datetime import datetime

router = APIRouter(prefix="/templates", tags=["templates"])

# ===============================================================
# GET /templates → Lista todos los templates del usuario logueado
# ===============================================================
@router.get("/")
def list_templates(db: Session = Depends(get_db), user=Depends(login_required)):
    q = select(Template).where(Template.owner_id == int(user["sub"]))
    rows = db.scalars(q).all()

    return [
        {
            "template_id": t.template_id,
            "name": t.name,
            "status": t.status,
            "placement_strategy": t.placement_strategy,
            "internet_egress": t.internet_egress,
            "created_at": t.created_at,
        }
        for t in rows
    ]


# ===============================================================
# POST /templates → Crea un nuevo template
# ===============================================================
@router.post("/")
async def create_template(request: Request, db: Session = Depends(get_db), user=Depends(login_required)):
    """
    Recibe un JSON desde el frontend con:
    {
        "slice_name": "Template1",
        "description": "Red en estrella",
        "topologia": { ... },
        "recursos": { ... }
    }
    """

    data = await request.json()
    name = data.get("slice_name", "Nuevo_Template")
    strategy = data.get("topologia", {}).get("type", "manual")
    internet_egress = bool(data.get("internet_egress", 0))

    t = Template(
        owner_id=int(user["sub"]),
        name=name,
        placement_strategy=strategy,
        internet_egress=internet_egress,
        created_by=int(user["sub"]),
        created_at=datetime.now(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    return {"ok": True, "template_id": t.template_id, "message": "Template guardado correctamente"}
