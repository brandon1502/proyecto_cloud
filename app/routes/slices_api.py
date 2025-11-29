# app/routes/slices_api.py
from typing import Optional, List
from datetime import datetime
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import login_required            # <- usamos el mismo que en /templates
from app.models import Slice, AvailabilityZone, Template

router = APIRouter(prefix="/slices", tags=["slices"])

# ===== Schemas =====
class SliceCreate(BaseModel):
    template_id: Optional[int] = Field(default=None)
    az_hint: Optional[str] = Field(
        default=None,
        description="Puede ser 'zone1', 'Zona 1', o un ID/Nombre que el backend intente resolver",
    )
    name: constr(strip_whitespace=True, min_length=1, max_length=150)

class SliceOut(BaseModel):
    slice_id: int
    name: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # pydantic v2

class SliceListItem(BaseModel):
    slice_id: int
    name: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    description: Optional[str] = None


# ===== Helpers =====
def resolve_az_id(db: Session, az_hint: Optional[str]) -> Optional[int]:
    """
    Mapea varios formatos a availability_zones.az_id:
      - 'zone1' -> busca 'Zona 1'
      - número -> usa como az_id
      - nombre exacto -> busca por name
    Si no encuentra, devuelve None.
    """
    if not az_hint:
        return None

    hint = str(az_hint).strip()

    # 'zoneN' -> 'Zona N'
    if hint.lower().startswith("zone") and hint[4:].isdigit():
        probable_name = f"Zona {hint[4:]}"
        az = db.execute(select(AvailabilityZone).where(AvailabilityZone.name == probable_name)).scalar_one_or_none()
        return az.az_id if az else None

    # dígito -> az_id directo
    if hint.isdigit():
        az = db.execute(select(AvailabilityZone).where(AvailabilityZone.az_id == int(hint))).scalar_one_or_none()
        return az.az_id if az else None

    # nombre exacto
    az = db.execute(select(AvailabilityZone).where(AvailabilityZone.name == hint)).scalar_one_or_none()
    return az.az_id if az else None


# ===== Endpoints =====
@router.get("", response_model=List[SliceListItem])
def list_slices(db: Session = Depends(get_db), user=Depends(login_required)):
    """
    Devuelve los slices del usuario autenticado, con una 'description' compuesta:
      - "<desc plantilla> · Zona: <nombre AZ>" si ambos existen
      - solo desc de plantilla
      - o "Zona: <nombre AZ>"
    """
    rows = (
        db.query(
            Slice.slice_id,
            Slice.name,
            Slice.status,
            Slice.created_at,
            Template.description.label("tpl_desc"),
            AvailabilityZone.name.label("az_name"),
        )
        .outerjoin(Template, Slice.template_id == Template.template_id)
        .outerjoin(AvailabilityZone, Slice.az_id == AvailabilityZone.az_id)
        .filter(Slice.owner_id == user.user_id)
        .order_by(Slice.created_at.desc())
        .all()
    )

    out: list[SliceListItem] = []
    for r in rows:
        desc = None
        if r.tpl_desc and r.az_name:
            desc = f"{r.tpl_desc} · Zona: {r.az_name}"
        elif r.tpl_desc:
            desc = r.tpl_desc
        elif r.az_name:
            desc = f"Zona: {r.az_name}"
        out.append(
            SliceListItem(
                slice_id=r.slice_id,
                name=r.name,
                status=r.status,
                created_at=r.created_at,
                description=desc,
            )
        )
    return out


@router.post("", response_model=SliceOut, status_code=status.HTTP_201_CREATED)
def create_slice(payload: SliceCreate, db: Session = Depends(get_db), user=Depends(login_required)):
    # Validar template si viene
    if payload.template_id:
        exists = db.execute(
            select(Template.template_id).where(Template.template_id == payload.template_id)
        ).scalar_one_or_none()
        if not exists:
            raise HTTPException(status_code=400, detail="template_id no existe")

    az_id = resolve_az_id(db, payload.az_hint)

    new_slice = Slice(
        owner_id=user.user_id,
        az_id=az_id,                               # puede ser None -> queda NULL
        template_id=payload.template_id or None,   # puede ser None -> NULL
        name=payload.name,
        status="active",                           # por defecto
        placement_strategy=None,
        sla_overcommit_cpu_pct=None,
        sla_overcommit_ram_pct=None,
        internet_egress=None,
        created_by=user.user_id,                   # si no lo quieres, pon None
    )

    db.add(new_slice)
    db.commit()
    db.refresh(new_slice)
    return SliceOut.model_validate(new_slice)


@router.get("/{slice_id}/details")
async def get_slice_details(
    slice_id: int,
    db: Session = Depends(get_db),
    user=Depends(login_required)
):
    """
    Obtiene todos los detalles de un slice desplegado incluyendo VMs, VLANs y puertos VNC.
    """
    # Verificar que el slice existe y pertenece al usuario
    slice_obj = db.execute(
        select(Slice).where(
            Slice.slice_id == slice_id,
            Slice.owner_id == user.user_id
        )
    ).scalar_one_or_none()
    
    if not slice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slice no encontrado o no tienes permisos"
        )
    
    # Obtener VMs, VLANs y puertos VNC del Resources API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Obtener VMs
            vms_response = await client.get(
                f"http://10.20.12.26:8001/api/v1/vms/?slice_id={slice_id}"
            )
            vms = vms_response.json() if vms_response.status_code == 200 else []
            
            # Obtener VLANs
            vlans_response = await client.get(
                f"http://10.20.12.26:8001/api/v1/vlans/?slice_id={slice_id}"
            )
            vlans = vlans_response.json() if vlans_response.status_code == 200 else []
            
            # Obtener puertos VNC
            vnc_response = await client.get(
                f"http://10.20.12.26:8001/api/v1/vnc-ports/?slice_id={slice_id}"
            )
            vnc_ports = vnc_response.json() if vnc_response.status_code == 200 else []
            
            return {
                "slice_id": slice_obj.slice_id,
                "name": slice_obj.name,
                "status": slice_obj.status,
                "template_id": slice_obj.template_id,
                "created_at": slice_obj.created_at,
                "vms": vms,
                "vlans": vlans,
                "vnc_ports": vnc_ports
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener detalles del slice: {str(e)}"
        )


@router.post("/{slice_id}/destroy", status_code=status.HTTP_200_OK)
async def destroy_slice(
    slice_id: int,
    db: Session = Depends(get_db),
    user=Depends(login_required)
):
    """
    Envía petición de destrucción al servidor de despliegue y elimina el slice de la BD.
    Además, libera automáticamente las VLANs y puertos VNC asociados.
    La operación de destrucción se ejecuta en background en el servidor.
    """
    # Verificar que el slice existe y pertenece al usuario
    slice_obj = db.execute(
        select(Slice).where(
            Slice.slice_id == slice_id,
            Slice.owner_id == user.user_id
        )
    ).scalar_one_or_none()
    
    if not slice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slice no encontrado o no tienes permisos"
        )
    
    # Guardar nombre para el mensaje de respuesta
    slice_name = slice_obj.name
    
    # 🆕 PRIMERO: Liberar VLANs y puertos VNC llamando a la Resources API
    resources_released = {"vlans": 0, "vnc_ports": 0}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Llamar al endpoint DELETE de la Resources API
            resources_url = f"http://10.20.12.26:8001/api/v1/slices/{slice_id}"
            resources_response = await client.delete(
                resources_url,
                params={
                    "deleted_by": user.user_id,
                    "delete_reason": "Usuario eliminó el slice desde la interfaz web"
                }
            )
            
            if resources_response.status_code == 200:
                resources_data = resources_response.json()
                resources_released["vlans"] = resources_data.get("detail", {}).get("vlans_released", 0)
                resources_released["vnc_ports"] = resources_data.get("detail", {}).get("vnc_ports_released", 0)
                print(f"✅ Recursos liberados: {resources_released['vlans']} VLANs, {resources_released['vnc_ports']} puertos VNC")
            else:
                print(f"⚠️ No se pudieron liberar recursos automáticamente: {resources_response.status_code}")
    except Exception as e:
        print(f"⚠️ Error al liberar recursos: {str(e)}")
        # Continuar con la destrucción aunque falle la liberación de recursos
    
    # Enviar POST al servidor de destrucción con timeout corto (5s para la respuesta inicial)
    deploy_url = "http://10.20.12.209:8581/destroy"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                deploy_url,
                headers={"Content-Type": "application/json"},
                params={"slice_id": slice_id}  # Enviar slice_id como query parameter
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error del servidor de despliegue: {error_detail}"
                )
            
            result = response.json()
            
            # Eliminar el slice de la base de datos
            db.delete(slice_obj)
            db.commit()
            
            return {
                "message": f"Slice '{slice_name}' eliminado exitosamente (destrucción en progreso)",
                "slice_id": slice_id,
                "deployment_response": result,
                "resources_released": resources_released
            }
            
    except httpx.TimeoutException:
        # Si da timeout, igual eliminamos el slice de la BD 
        # porque la destrucción está procesándose en el servidor
        db.delete(slice_obj)
        db.commit()
        
        return {
            "message": f"Slice '{slice_name}' eliminado de la base de datos (destrucción en progreso)",
            "slice_id": slice_id,
            "note": "La operación de destrucción continúa en el servidor aunque no haya respondido a tiempo",
            "resources_released": resources_released
        }
        
    except httpx.RequestError as e:
        # Error de conexión: NO eliminamos de la BD
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de conexión con servidor de despliegue: {str(e)}"
        )
