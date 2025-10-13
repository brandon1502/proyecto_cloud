# app/routers/templates.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Template, TemplateVM, TemplateEdge, Flavour
from app.deps import login_required
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import func, Float, cast

# extras para export/serialización
import json
import re

router = APIRouter(prefix="/templates", tags=["templates"])

# ---------- Schemas para crear template ----------
class VMConfigRequest(BaseModel):
    name: str
    flavour: str         # ej. "small"
    image: str
    internet: bool = False

class NodeRequest(BaseModel):
    id: str
    label: str
    x: Optional[float] = None
    y: Optional[float] = None

class EdgeRequest(BaseModel):
    id: str
    from_node: str = Field(alias="from")
    to: str
    model_config = ConfigDict(populate_by_name=True)

class TopologyRequest(BaseModel):
    nodes: List[NodeRequest]
    edges: List[EdgeRequest]

class TemplateCreateRequest(BaseModel):
    slice_name: str
    description: Optional[str] = None
    topologia: TopologyRequest
    recursos: dict  # { node_id: {name, flavour, image, internet, ...} }

# ---------- util común: construir JSON desde BD ----------
def _build_template_json_from_db(db: Session, template_id: int) -> dict:
    """
    Arma el JSON EXACTO pedido:
    {
      "topologia": { "nodes": [...], "edges": [...] },
      "recursos": { "vm-1": {...}, ... },
      "subred": { "public_access": [...] }
    }
    Numeramos las VMs como vm-1..vm-N según orden por template_vm_id.
    """
    # VMs + flavour
    rows: List[Tuple[TemplateVM, Flavour]] = (
        db.query(TemplateVM, Flavour)
        .join(Flavour, Flavour.flavour_id == TemplateVM.flavour_id)
        .filter(TemplateVM.template_id == template_id)
        .order_by(TemplateVM.template_vm_id.asc())
        .all()
    )

    nodes = []
    recursos: Dict[str, dict] = {}
    public_access_ids: List[str] = []
    id_map: Dict[int, str] = {}

    for i, (vm, fl) in enumerate(rows, start=1):
        vm_id = f"vm-{i}"
        id_map[vm.template_vm_id] = vm_id

        nodes.append({
            "id": vm_id,
            "label": vm.name,
            "shape": "image",
            "image": "/static/images/pc.png",
        })

        recursos[vm_id] = {
            "name": vm.name,
            "ram_gb": float(fl.ram_gb),
            "vcpu": int(fl.vcpu),
            "disk_gb": float(fl.disk_gb),
            "os": (vm.imagen or "ubuntu").lower(),
            "flavour": fl.name,     # 👈 requerido
        }

        if bool(vm.public_access):
            public_access_ids.append(vm_id)

    # Edges
    edge_rows = (
        db.query(TemplateEdge)
        .filter(TemplateEdge.template_id == template_id)
        .all()
    )
    edges = []
    for e in edge_rows:
        f = id_map.get(e.from_vm_id)
        t = id_map.get(e.to_vm_id)
        if f and t:
            edges.append({"id": f"edge-{f}-{t}", "from": f, "to": t})

    return {
        "topologia": {"nodes": nodes, "edges": edges},
        "recursos": recursos,
        "subred": {"public_access": public_access_ids},
    }

# ---------- Crear template ----------
@router.post("")
def create_template(
    data: TemplateCreateRequest,
    db: Session = Depends(get_db),
    user = Depends(login_required),   # <- ORM User
):
    try:
        # 1) cabecera del template
        tpl = Template(
            user_id=user.user_id,
            name=data.slice_name,
            description=data.description,
        )
        db.add(tpl)
        db.flush()  # ya tenemos tpl.template_id

        # 2) VMs del template
        node_to_vm: dict[str, int] = {}
        for node in data.topologia.nodes:
            vm_cfg = data.recursos.get(node.id)
            if not vm_cfg:
                continue

            flavour = (
                db.query(Flavour)
                .filter(Flavour.name == vm_cfg["flavour"])
                .first()
            )
            if not flavour:
                raise HTTPException(
                    status_code=400,
                    detail=f"Flavour '{vm_cfg['flavour']}' no encontrado",
                )

            vm = TemplateVM(
                template_id=tpl.template_id,
                flavour_id=flavour.flavour_id,
                name=vm_cfg["name"],
                imagen=vm_cfg.get("image", "Ubuntu"),
                public_access=bool(vm_cfg.get("internet", False)),
            )
            db.add(vm)
            db.flush()
            node_to_vm[node.id] = vm.template_vm_id

        # 3) Conexiones
        for e in data.topologia.edges:
            f_id = node_to_vm.get(e.from_node)
            t_id = node_to_vm.get(e.to)
            if f_id and t_id:
                db.add(TemplateEdge(
                    template_id=tpl.template_id,
                    from_vm_id=f_id,
                    to_vm_id=t_id
                ))

        db.flush()

        # 4) 🔥 Generar JSON y guardarlo en templates.json_template
        tpl.json_template = _build_template_json_from_db(db, tpl.template_id)

        # 5) commit final
        db.commit()

        return {
            "success": True,
            "template_id": tpl.template_id,
            "message": "Template creado y JSON guardado exitosamente",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))

# ---------- Listar templates ----------
@router.get("")
def list_templates(
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    rows = (
        db.query(
            Template.template_id.label("template_id"),
            Template.name.label("name"),
            Template.description.label("description"),
            Template.created_at.label("created_at"),
            Template.updated_last_at.label("updated_last_at"),
            func.count(TemplateVM.template_vm_id).label("vm_count"),
            func.coalesce(func.sum(Flavour.vcpu), 0).label("sum_vcpu"),
            func.coalesce(func.sum(cast(Flavour.ram_gb, Float)), 0.0).label("sum_ram_gb"),
            func.coalesce(func.sum(cast(Flavour.disk_gb, Float)), 0.0).label("sum_disk_gb"),
        )
        .outerjoin(TemplateVM, TemplateVM.template_id == Template.template_id)
        .outerjoin(Flavour, Flavour.flavour_id == TemplateVM.flavour_id)
        .filter(Template.user_id == user.user_id)
        .group_by(Template.template_id)
        .order_by(Template.created_at.desc())
        .all()
    )

    return [
        {
            "template_id": r.template_id,
            "name": r.name,
            "description": r.description,
            "created_at": r.created_at,
            "updated_last_at": r.updated_last_at,
            "vm_count": int(r.vm_count or 0),
            "sum_vcpu": int(r.sum_vcpu or 0),
            "sum_ram_gb": float(r.sum_ram_gb or 0.0),
            "sum_disk_gb": float(r.sum_disk_gb or 0.0),
        }
        for r in rows
    ]

# ---------- Exportar template como JSON (descarga) ----------
_slug_rx = re.compile(r"[^a-z0-9]+")
def _slugify(s: str) -> str:
    return _slug_rx.sub("-", (s or "").lower()).strip("-") or "template"

# Exportar EXACTAMENTE lo guardado en DB (sin regenerar)
@router.get("/{template_id}/export")
def export_template_json_db(
    template_id: int,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    tpl = (
        db.query(Template)
        .filter(Template.template_id == template_id, Template.user_id == user.user_id)
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    if not tpl.json_template:
        # Aquí preferimos fallar explícito para “comprobar” que efectivamente lo guarda
        raise HTTPException(
            status_code=409,
            detail="El template no tiene JSON guardado aún. Guarda la topología primero."
        )

    filename = f"{re.sub(r'[^a-z0-9]+','-', (tpl.name or '').lower()).strip('-') or 'template'}_{template_id}.json"
    return Response(
        content=json.dumps(tpl.json_template, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

