"""
Endpoints para gestión de puertos VNC
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import VNCPort
from ..schemas import (
    VNCPortResponse,
    VNCPortBase,
    VNCPortReserveRequest,
    VNCPortReleaseRequest,
    MessageResponse
)

router = APIRouter()


@router.get("/available", response_model=List[VNCPortResponse])
async def get_available_vnc_ports(
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Obtener puertos VNC disponibles (no usados)
    
    - **az_id**: (Opcional) Filtrar por zona de disponibilidad
    - **limit**: Límite de resultados (default: 100, max: 1000)
    """
    query = db.query(VNCPort).filter(VNCPort.is_used == False)
    
    if az_id is not None:
        query = query.filter(VNCPort.az_id == az_id)
    
    ports = query.limit(limit).all()
    return ports


@router.get("/", response_model=List[VNCPortResponse])
async def get_all_vnc_ports(
    is_used: Optional[bool] = Query(None, description="Filtrar por estado de uso"),
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    vm_id: Optional[int] = Query(None, description="Filtrar por VM"),
    slice_id: Optional[int] = Query(None, description="Filtrar por slice"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los puertos VNC con filtros opcionales
    """
    query = db.query(VNCPort)
    
    if is_used is not None:
        query = query.filter(VNCPort.is_used == is_used)
    if az_id is not None:
        query = query.filter(VNCPort.az_id == az_id)
    if vm_id is not None:
        query = query.filter(VNCPort.vm_id == vm_id)
    if slice_id is not None:
        query = query.filter(VNCPort.slice_id == slice_id)
    
    ports = query.offset(offset).limit(limit).all()
    return ports


@router.get("/{vnc_port_id}", response_model=VNCPortResponse)
async def get_vnc_port(
    vnc_port_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información de un puerto VNC específico por ID
    """
    port = db.query(VNCPort).filter(VNCPort.vnc_port_id == vnc_port_id).first()
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Puerto VNC con ID {vnc_port_id} no encontrado"
        )
    return port


@router.post("/", response_model=VNCPortResponse, status_code=status.HTTP_201_CREATED)
async def create_vnc_port(
    port: VNCPortBase,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo puerto VNC
    
    - **port_number**: Número de puerto VNC
    - **az_id**: (Opcional) ID de la zona de disponibilidad
    - **description**: (Opcional) Descripción del puerto
    """
    # Verificar que no exista puerto con el mismo número en la misma AZ
    existing = db.query(VNCPort).filter(
        and_(
            VNCPort.port_number == port.port_number,
            VNCPort.az_id == port.az_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un puerto VNC {port.port_number} en esta zona"
        )
    
    new_port = VNCPort(
        port_number=port.port_number,
        az_id=port.az_id,
        description=port.description,
        is_used=False
    )
    
    db.add(new_port)
    db.commit()
    db.refresh(new_port)
    
    return new_port


@router.post("/reserve", response_model=VNCPortResponse)
async def reserve_vnc_port(
    request: VNCPortReserveRequest,
    db: Session = Depends(get_db)
):
    """
    Reservar (marcar como usado) un puerto VNC
    
    - **vnc_port_id**: ID del puerto VNC a reservar
    - **vm_id**: (Opcional) ID de la VM que usa el puerto
    - **slice_id**: (Opcional) ID del slice
    - **reserved_by**: (Opcional) ID del usuario que reserva
    - **description**: (Opcional) Descripción/motivo de reserva
    """
    port = db.query(VNCPort).filter(VNCPort.vnc_port_id == request.vnc_port_id).first()
    
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Puerto VNC con ID {request.vnc_port_id} no encontrado"
        )
    
    # Si ya está en uso, permitir actualizar vm_id o slice_id si vienen en el request
    if port.is_used:
        # Permitir actualizar si está reservado pero sin VM/slice asignado
        can_update = False
        if request.vm_id and port.vm_id is None:
            port.vm_id = request.vm_id
            can_update = True
        if request.slice_id and port.slice_id is None:
            port.slice_id = request.slice_id
            can_update = True
        
        if not can_update:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Puerto VNC {port.port_number} ya está en uso"
            )
    else:
        # Reservar puerto por primera vez
        port.is_used = True
        port.vm_id = request.vm_id
        port.slice_id = request.slice_id
        port.reserved_by = request.reserved_by
        port.reserved_at = datetime.utcnow()
    
    if request.description:
        port.description = request.description
    
    db.commit()
    db.refresh(port)
    
    return port


@router.post("/release", response_model=MessageResponse)
async def release_vnc_port(
    request: VNCPortReleaseRequest,
    db: Session = Depends(get_db)
):
    """
    Liberar (marcar como disponible) un puerto VNC y resetear todos sus atributos
    
    - **vnc_port_id**: ID del puerto VNC a liberar
    
    Al liberar, resetea: is_used=0, vm_id=NULL, slice_id=NULL, 
    reserved_at=NULL, reserved_by=NULL, released_at=NULL, description=NULL, az_id=NULL
    """
    port = db.query(VNCPort).filter(VNCPort.vnc_port_id == request.vnc_port_id).first()
    
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Puerto VNC con ID {request.vnc_port_id} no encontrado"
        )
    
    # Liberar puerto y resetear TODOS los atributos a valores por defecto
    port.is_used = False
    port.vm_id = None
    port.slice_id = None
    port.reserved_at = None
    port.reserved_by = None
    port.released_at = None
    port.description = None
    port.az_id = None
    
    db.commit()
    
    print(f"🔓 Puerto VNC {port.port_number} liberado completamente (todos atributos reseteados)")
    
    return MessageResponse(
        message=f"Puerto VNC {port.port_number} liberado exitosamente",
        detail={"vnc_port_id": port.vnc_port_id, "port_number": port.port_number}
    )


@router.delete("/{vnc_port_id}", response_model=MessageResponse)
async def delete_vnc_port(
    vnc_port_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar un puerto VNC (solo si no está en uso)
    """
    port = db.query(VNCPort).filter(VNCPort.vnc_port_id == vnc_port_id).first()
    
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Puerto VNC con ID {vnc_port_id} no encontrado"
        )
    
    if port.is_used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un puerto VNC en uso. Primero libérelo."
        )
    
    db.delete(port)
    db.commit()
    
    return MessageResponse(
        message=f"Puerto VNC {port.port_number} eliminado exitosamente",
        detail={"vnc_port_id": vnc_port_id}
    )
