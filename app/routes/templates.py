# app/routers/templates.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Template, TemplateVM, TemplateEdge, Flavour
from app.deps import login_required
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import func, Float, cast
import json
import re

router = APIRouter(prefix="/templates", tags=["templates"])

# Schemas
class VMConfigRequest(BaseModel):
    name: str
    flavour: str
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
    recursos: dict

class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    json_template: Optional[dict] = None

def _build_template_json_from_db(db: Session, template_id: int) -> dict:
    """
    Construye el JSON del template desde la base de datos
    """
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
            "flavour": fl.name,
        }

        if bool(vm.public_access):
            public_access_ids.append(vm_id)

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

@router.post("/guardar")
def create_template(
    data: TemplateCreateRequest,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    try:
        tpl = Template(
            user_id=user.user_id,
            name=data.slice_name,
            description=data.description,
        )
        db.add(tpl)
        db.flush()

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
        tpl.json_template = _build_template_json_from_db(db, tpl.template_id)
        db.commit()

        return {
            "success": True,
            "template_id": tpl.template_id,
            "message": "Template creado exitosamente",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))

@router.get("/mostrar_plantilla")
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

@router.get("/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    tpl = (
        db.query(Template)
        .filter(
            Template.template_id == template_id,
            Template.user_id == user.user_id
        )
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    agg = (
        db.query(
            func.coalesce(func.sum(Flavour.vcpu), 0).label("sum_vcpu"),
            func.coalesce(func.sum(cast(Flavour.ram_gb, Float)), 0.0).label("sum_ram_gb"),
            func.coalesce(func.sum(cast(Flavour.disk_gb, Float)), 0.0).label("sum_disk_gb"),
        )
        .join(TemplateVM, TemplateVM.flavour_id == Flavour.flavour_id)
        .filter(TemplateVM.template_id == tpl.template_id)
        .first()
    )

    return {
        "template_id": tpl.template_id,
        "name": tpl.name,
        "description": tpl.description,
        "created_at": tpl.created_at,
        "updated_last_at": tpl.updated_last_at,
        "sum_vcpu": int(agg.sum_vcpu or 0),
        "sum_ram_gb": float(agg.sum_ram_gb or 0.0),
        "sum_disk_gb": float(agg.sum_disk_gb or 0.0),
        "json_template": tpl.json_template,
    }

@router.put("/{template_id}")
def update_template(
    template_id: int,
    payload: TemplateUpdateRequest,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    """
    Actualiza un template existente.
    Si se proporciona json_template, también reconstruye las VMs y edges en la BD.
    """
    tpl = (
        db.query(Template)
        .filter(Template.template_id == template_id, Template.user_id == user.user_id)
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    try:
        # Actualizar metadatos básicos
        if payload.name is not None:
            tpl.name = payload.name
        if payload.description is not None:
            tpl.description = payload.description

        # Si hay json_template nuevo, reconstruir completamente
        if payload.json_template is not None:
            # 1. Eliminar VMs y edges antiguos
            db.query(TemplateEdge).filter(
                TemplateEdge.template_id == template_id
            ).delete()
            
            db.query(TemplateVM).filter(
                TemplateVM.template_id == template_id
            ).delete()
            
            db.flush()

            # 2. Recrear desde el JSON
            json_tpl = payload.json_template
            topologia = json_tpl.get("topologia", {})
            recursos = json_tpl.get("recursos", {})
            public_access_list = json_tpl.get("subred", {}).get("public_access", [])

            node_to_vm: dict[str, int] = {}

            # Crear VMs
            if "nodes" in topologia:
                for node in topologia["nodes"]:
                    node_id = node["id"]
                    recurso = recursos.get(node_id)
                    
                    if not recurso:
                        continue

                    # Buscar flavour
                    flavour = (
                        db.query(Flavour)
                        .filter(Flavour.name == recurso.get("flavour", "small"))
                        .first()
                    )
                    
                    if not flavour:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Flavour '{recurso.get('flavour')}' no encontrado"
                        )

                    vm = TemplateVM(
                        template_id=template_id,
                        flavour_id=flavour.flavour_id,
                        name=recurso.get("name", node.get("label", node_id)),
                        imagen=recurso.get("os", "Ubuntu"),
                        public_access=node_id in public_access_list,
                    )
                    db.add(vm)
                    db.flush()
                    node_to_vm[node_id] = vm.template_vm_id

            # Crear edges
            if "edges" in topologia:
                for edge in topologia["edges"]:
                    from_id = node_to_vm.get(edge["from"])
                    to_id = node_to_vm.get(edge["to"])
                    
                    if from_id and to_id:
                        db.add(TemplateEdge(
                            template_id=template_id,
                            from_vm_id=from_id,
                            to_vm_id=to_id
                        ))

            db.flush()

            # 3. Guardar el JSON actualizado
            tpl.json_template = payload.json_template

        tpl.updated_last_at = func.current_timestamp()
        db.add(tpl)
        db.commit()
        db.refresh(tpl)

        return {"success": True, "template_id": tpl.template_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))

@router.delete("/{template_id}")
def delete_template(
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

    db.delete(tpl)
    db.commit()

    return {"success": True, "template_id": template_id}

@router.get("/{template_id}/export")
def export_template_json(
    template_id: int,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    """
    Exporta el template como archivo JSON descargable
    """
    tpl = (
        db.query(Template)
        .filter(Template.template_id == template_id, Template.user_id == user.user_id)
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    if not tpl.json_template:
        raise HTTPException(
            status_code=409,
            detail="El template no tiene JSON guardado."
        )

    filename = f"{re.sub(r'[^a-z0-9]+','-', (tpl.name or '').lower()).strip('-') or 'template'}_{template_id}.json"
    
    return Response(
        content=json.dumps(tpl.json_template, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )