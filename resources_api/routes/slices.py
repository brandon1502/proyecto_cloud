"""
Endpoints para gestión de Slices (guardar datos de deployment)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Slice
from ..schemas import (
    SliceResponse,
    SliceCreateRequest,
    SliceUpdateRequest,
    MessageResponse
)

router = APIRouter()


@router.get("/", response_model=List[SliceResponse])
async def get_all_slices(
    owner_id: Optional[int] = Query(None, description="Filtrar por dueño"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los slices con filtros opcionales
    """
    query = db.query(Slice)
    
    if owner_id is not None:
        query = query.filter(Slice.owner_id == owner_id)
    if status is not None:
        query = query.filter(Slice.status == status)
    if az_id is not None:
        query = query.filter(Slice.az_id == az_id)
    
    # Filtrar solo slices no eliminados
    query = query.filter(Slice.deleted_at.is_(None))
    
    slices = query.offset(offset).limit(limit).all()
    return slices


@router.get("/{slice_id}", response_model=SliceResponse)
async def get_slice(
    slice_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información de un slice específico por ID
    """
    slice_obj = db.query(Slice).filter(
        Slice.slice_id == slice_id,
        Slice.deleted_at.is_(None)
    ).first()
    
    if not slice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slice con ID {slice_id} no encontrado"
        )
    return slice_obj


@router.post("/", response_model=SliceResponse, status_code=status.HTTP_201_CREATED)
async def create_slice(
    slice_data: SliceCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo slice (después de deployment exitoso)
    
    - **owner_id**: ID del usuario dueño (obligatorio)
    - **name**: Nombre del slice (obligatorio)
    - **az_id**: Zona de disponibilidad (opcional)
    - **template_id**: ID de la plantilla usada (opcional)
    - **status**: Estado del slice (default: 'active')
    - **placement_strategy**: Estrategia de placement (opcional)
    - **sla_overcommit_cpu_pct**: Overcommit de CPU (opcional)
    - **sla_overcommit_ram_pct**: Overcommit de RAM (opcional)
    - **internet_egress**: Acceso a internet (default: False)
    - **created_by**: ID del usuario que lo creó (opcional)
    
    NOTA: Evita duplicados buscando slices del mismo owner/template creados recientemente (últimos 10 segundos).
    """
    # Verificar si ya existe un slice reciente del mismo owner y template (últimos 10 segundos)
    # Esto previene duplicados cuando el deployment server llama 2 veces
    from sqlalchemy import and_
    from datetime import datetime, timedelta
    
    # LOG DETALLADO para debugging
    print(f"🔍 CREATE SLICE REQUEST - owner_id={slice_data.owner_id}, template_id={slice_data.template_id}, name={slice_data.name}")
    
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    
    existing_slice = db.query(Slice).filter(
        and_(
            Slice.owner_id == slice_data.owner_id,
            Slice.template_id == slice_data.template_id,
            Slice.deleted_at.is_(None),
            Slice.created_at >= ten_seconds_ago
        )
    ).first()
    
    if existing_slice:
        # Retornar el slice existente (idempotencia)
        print(f"✅ DUPLICATE DETECTED - Returning existing slice_id={existing_slice.slice_id}")
        return existing_slice
    
    print(f"➕ CREATING NEW SLICE - owner_id={slice_data.owner_id}, template_id={slice_data.template_id}")
    
    new_slice = Slice(
        owner_id=slice_data.owner_id,
        name=slice_data.name,
        az_id=slice_data.az_id,
        template_id=slice_data.template_id,
        status=slice_data.status or 'active',
        placement_strategy=slice_data.placement_strategy,
        sla_overcommit_cpu_pct=slice_data.sla_overcommit_cpu_pct,
        sla_overcommit_ram_pct=slice_data.sla_overcommit_ram_pct,
        internet_egress=slice_data.internet_egress or False,
        created_at=datetime.utcnow(),
        created_by=slice_data.created_by
    )
    
    db.add(new_slice)
    db.commit()
    db.refresh(new_slice)
    
    return new_slice


@router.put("/{slice_id}", response_model=SliceResponse)
async def update_slice(
    slice_id: int,
    slice_data: SliceUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar un slice existente
    
    - **status**: Nuevo estado del slice
    - **updated_by**: ID del usuario que actualiza
    """
    slice_obj = db.query(Slice).filter(
        Slice.slice_id == slice_id,
        Slice.deleted_at.is_(None)
    ).first()
    
    if not slice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slice con ID {slice_id} no encontrado"
        )
    
    # Actualizar campos
    if slice_data.status is not None:
        slice_obj.status = slice_data.status
    if slice_data.placement_strategy is not None:
        slice_obj.placement_strategy = slice_data.placement_strategy
    if slice_data.sla_overcommit_cpu_pct is not None:
        slice_obj.sla_overcommit_cpu_pct = slice_data.sla_overcommit_cpu_pct
    if slice_data.sla_overcommit_ram_pct is not None:
        slice_obj.sla_overcommit_ram_pct = slice_data.sla_overcommit_ram_pct
    if slice_data.internet_egress is not None:
        slice_obj.internet_egress = slice_data.internet_egress
    
    slice_obj.updated_at = datetime.utcnow()
    slice_obj.updated_by = slice_data.updated_by
    
    db.commit()
    db.refresh(slice_obj)
    
    return slice_obj


@router.delete("/{slice_id}", response_model=MessageResponse)
async def delete_slice(
    slice_id: int,
    deleted_by: Optional[int] = Query(None, description="ID del usuario que elimina"),
    delete_reason: Optional[str] = Query(None, description="Razón de eliminación"),
    db: Session = Depends(get_db)
):
    """
    Eliminar un slice (soft delete) y liberar recursos asociados
    
    Al eliminar un slice, automáticamente:
    - Libera todas las VLANs asociadas (is_used=0, slice_id=NULL)
    - Libera todos los puertos VNC asociados (is_used=0, vm_id=NULL, slice_id=NULL)
    - Marca el slice como eliminado (soft delete)
    """
    from ..models import VLAN, VNCPort
    
    slice_obj = db.query(Slice).filter(
        Slice.slice_id == slice_id,
        Slice.deleted_at.is_(None)
    ).first()
    
    if not slice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slice con ID {slice_id} no encontrado"
        )
    
    # 1. Liberar VLANs asociadas al slice (resetear TODOS los atributos)
    vlans_released = db.query(VLAN).filter(
        VLAN.slice_id == slice_id
    ).update({
        "is_used": 0,
        "slice_id": None,
        "reserved_at": None,
        "reserved_by": None,
        "released_at": None,
        "description": None,
        "az_id": None
    }, synchronize_session=False)
    
    # 2. Liberar puertos VNC asociados al slice (resetear TODOS los atributos)
    vnc_ports_released = db.query(VNCPort).filter(
        VNCPort.slice_id == slice_id
    ).update({
        "is_used": 0,
        "vm_id": None,
        "slice_id": None,
        "reserved_at": None,
        "reserved_by": None,
        "released_at": None,
        "description": None,
        "az_id": None
    }, synchronize_session=False)
    
    # 3. Soft delete del slice
    slice_obj.deleted_at = datetime.utcnow()
    slice_obj.deleted_by = deleted_by
    slice_obj.delete_reason = delete_reason
    slice_obj.status = 'deleted'
    
    db.commit()
    
    print(f"🗑️ SLICE DELETED - slice_id={slice_id}, VLANs liberadas={vlans_released}, Puertos VNC liberados={vnc_ports_released}")
    
    return MessageResponse(
        message=f"Slice '{slice_obj.name}' eliminado exitosamente",
        detail={
            "slice_id": slice_id,
            "name": slice_obj.name,
            "vlans_released": vlans_released,
            "vnc_ports_released": vnc_ports_released
        }
    )
