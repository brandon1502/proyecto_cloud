"""
Endpoints para gestión de VLANs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import logging

from ..database import get_db
from ..models import VLAN
from ..schemas import (
    VLANResponse, 
    VLANBase,
    VLANReserveRequest, 
    VLANReleaseRequest,
    MessageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/available", response_model=List[VLANResponse])
async def get_available_vlans(
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Obtener VLANs disponibles (no usadas)
    
    - **az_id**: (Opcional) Filtrar por zona de disponibilidad
    - **limit**: Límite de resultados (default: 100, max: 1000)
    """
    query = db.query(VLAN).filter(VLAN.is_used == False)
    
    if az_id is not None:
        query = query.filter(VLAN.az_id == az_id)
    
    vlans = query.limit(limit).all()
    return vlans


@router.get("/", response_model=List[VLANResponse])
async def get_all_vlans(
    is_used: Optional[bool] = Query(None, description="Filtrar por estado de uso"),
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    slice_id: Optional[int] = Query(None, description="Filtrar por slice"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las VLANs con filtros opcionales
    """
    query = db.query(VLAN)
    
    if is_used is not None:
        query = query.filter(VLAN.is_used == is_used)
    if az_id is not None:
        query = query.filter(VLAN.az_id == az_id)
    if slice_id is not None:
        query = query.filter(VLAN.slice_id == slice_id)
    
    vlans = query.offset(offset).limit(limit).all()
    return vlans


@router.get("/{vlan_id}", response_model=VLANResponse)
async def get_vlan(
    vlan_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información de una VLAN específica por ID
    """
    vlan = db.query(VLAN).filter(VLAN.vlan_id == vlan_id).first()
    if not vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN con ID {vlan_id} no encontrada"
        )
    return vlan


@router.post("/", response_model=VLANResponse, status_code=status.HTTP_201_CREATED)
async def create_vlan(
    vlan: VLANBase,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva VLAN
    
    - **vlan_number**: Número de VLAN (1-4094)
    - **az_id**: (Opcional) ID de la zona de disponibilidad
    - **description**: (Opcional) Descripción de la VLAN
    """
    # Verificar que no exista VLAN con el mismo número en la misma AZ
    existing = db.query(VLAN).filter(
        and_(
            VLAN.vlan_number == vlan.vlan_number,
            VLAN.az_id == vlan.az_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una VLAN con número {vlan.vlan_number} en esta zona"
        )
    
    new_vlan = VLAN(
        vlan_number=vlan.vlan_number,
        az_id=vlan.az_id,
        description=vlan.description,
        is_used=False
    )
    
    db.add(new_vlan)
    db.commit()
    db.refresh(new_vlan)
    
    return new_vlan


@router.post("/reserve", response_model=VLANResponse)
async def reserve_vlan(
    request: VLANReserveRequest,
    db: Session = Depends(get_db)
):
    """
    Reservar (marcar como usada) una VLAN
    
    - **vlan_id**: ID de la VLAN a reservar
    - **slice_id**: (Opcional) ID del slice que reserva
    - **reserved_by**: (Opcional) ID del usuario que reserva
    - **description**: (Opcional) Descripción/motivo de reserva
    """
    logger.info(f"🔵 RESERVE REQUEST: vlan_id={request.vlan_id}, slice_id={request.slice_id}, reserved_by={request.reserved_by}")
    
    vlan = db.query(VLAN).filter(VLAN.vlan_id == request.vlan_id).first()
    
    if not vlan:
        logger.error(f"❌ VLAN {request.vlan_id} no encontrada")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN con ID {request.vlan_id} no encontrada"
        )
    
    # Si ya está en uso, permitir actualizar el slice_id si viene en el request
    if vlan.is_used:
        # Permitir actualizar slice_id si la VLAN ya está reservada pero sin slice asignado
        if request.slice_id and vlan.slice_id is None:
            logger.info(f"🔄 Actualizando VLAN {vlan.vlan_number} con slice_id={request.slice_id}")
            vlan.slice_id = request.slice_id
        else:
            logger.warning(f"⚠️ VLAN {vlan.vlan_number} ya está en uso con slice_id={vlan.slice_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"VLAN {vlan.vlan_number} ya está en uso"
            )
    else:
        # Reservar VLAN por primera vez
        vlan.is_used = True
        vlan.slice_id = request.slice_id
        vlan.reserved_by = request.reserved_by
        vlan.reserved_at = datetime.utcnow()
    
    if request.description:
        vlan.description = request.description
    
    try:
        db.commit()
        db.refresh(vlan)
        logger.info(f"✅ VLAN {vlan.vlan_number} reservada exitosamente")
        return vlan
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al reservar VLAN: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reservar VLAN: {str(e)}"
        )


@router.post("/release", response_model=MessageResponse)
async def release_vlan(
    request: VLANReleaseRequest,
    db: Session = Depends(get_db)
):
    """
    Liberar (marcar como disponible) una VLAN y resetear todos sus atributos
    
    - **vlan_id**: ID de la VLAN a liberar
    
    Al liberar, resetea: is_used=0, slice_id=NULL, reserved_at=NULL, 
    reserved_by=NULL, released_at=NULL, description=NULL, az_id=NULL
    """
    vlan = db.query(VLAN).filter(VLAN.vlan_id == request.vlan_id).first()
    
    if not vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN con ID {request.vlan_id} no encontrada"
        )
    
    # Liberar VLAN y resetear TODOS los atributos a valores por defecto
    vlan.is_used = False
    vlan.slice_id = None
    vlan.reserved_at = None
    vlan.reserved_by = None
    vlan.released_at = None
    vlan.description = None
    vlan.az_id = None
    
    db.commit()
    
    logger.info(f"🔓 VLAN {vlan.vlan_number} liberada completamente (todos atributos reseteados)")
    
    return MessageResponse(
        message=f"VLAN {vlan.vlan_number} liberada exitosamente",
        detail={"vlan_id": vlan.vlan_id, "vlan_number": vlan.vlan_number}
    )


@router.delete("/{vlan_id}", response_model=MessageResponse)
async def delete_vlan(
    vlan_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar una VLAN (solo si no está en uso)
    """
    vlan = db.query(VLAN).filter(VLAN.vlan_id == vlan_id).first()
    
    if not vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN con ID {vlan_id} no encontrada"
        )
    
    if vlan.is_used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una VLAN en uso. Primero libérela."
        )
    
    db.delete(vlan)
    db.commit()
    
    return MessageResponse(
        message=f"VLAN {vlan.vlan_number} eliminada exitosamente",
        detail={"vlan_id": vlan_id}
    )
