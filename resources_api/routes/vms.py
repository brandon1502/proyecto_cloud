"""
Endpoints para gestión de VMs (guardar datos de VMs desplegadas)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import VM
from ..schemas import (
    VMResponse,
    VMCreateRequest,
    VMUpdateRequest,
    MessageResponse
)

router = APIRouter()


@router.get("/", response_model=List[VMResponse])
async def get_all_vms(
    slice_id: Optional[int] = Query(None, description="Filtrar por slice"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    az_id: Optional[int] = Query(None, description="Filtrar por zona de disponibilidad"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las VMs con filtros opcionales
    """
    query = db.query(VM)
    
    if slice_id is not None:
        query = query.filter(VM.slice_id == slice_id)
    if status is not None:
        query = query.filter(VM.status == status)
    if az_id is not None:
        query = query.filter(VM.az_id == az_id)
    
    # Filtrar solo VMs no eliminadas
    query = query.filter(VM.deleted_at.is_(None))
    
    vms = query.offset(offset).limit(limit).all()
    return vms


@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener información de una VM específica por ID
    """
    vm = db.query(VM).filter(
        VM.vm_id == vm_id,
        VM.deleted_at.is_(None)
    ).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM con ID {vm_id} no encontrada"
        )
    return vm


@router.post("/", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    vm_data: VMCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva VM (después de deployment exitoso)
    
    - **slice_id**: ID del slice al que pertenece (obligatorio)
    - **image_id**: ID de la imagen usada (obligatorio)
    - **name**: Nombre de la VM (obligatorio)
    - **vcpu**: Número de vCPUs (obligatorio)
    - **ram_mb**: RAM en MB (obligatorio)
    - **disk_gb**: Disco en GB (obligatorio)
    - **az_id**: Zona de disponibilidad (opcional)
    - **status**: Estado de la VM (default: 'running')
    - **worker_ip**: IP del worker donde está la VM (opcional)
    - **created_by**: ID del usuario que la creó (opcional)
    """
    new_vm = VM(
        slice_id=vm_data.slice_id,
        image_id=vm_data.image_id,
        name=vm_data.name,
        vcpu=vm_data.vcpu,
        ram_mb=vm_data.ram_mb,
        disk_gb=vm_data.disk_gb,
        az_id=vm_data.az_id,
        status=vm_data.status or 'running',
        worker_ip=vm_data.worker_ip,
        created_at=datetime.utcnow(),
        created_by=vm_data.created_by
    )
    
    db.add(new_vm)
    db.commit()
    db.refresh(new_vm)
    
    return new_vm


@router.put("/{vm_id}", response_model=VMResponse)
async def update_vm(
    vm_id: int,
    vm_data: VMUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar una VM existente
    
    - **status**: Nuevo estado de la VM
    - **worker_ip**: IP del worker donde está la VM
    - **updated_by**: ID del usuario que actualiza
    """
    vm = db.query(VM).filter(
        VM.vm_id == vm_id,
        VM.deleted_at.is_(None)
    ).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM con ID {vm_id} no encontrada"
        )
    
    # Actualizar campos
    if vm_data.status is not None:
        vm.status = vm_data.status
    if vm_data.vcpu is not None:
        vm.vcpu = vm_data.vcpu
    if vm_data.ram_mb is not None:
        vm.ram_mb = vm_data.ram_mb
    if vm_data.disk_gb is not None:
        vm.disk_gb = vm_data.disk_gb
    if vm_data.worker_ip is not None:
        vm.worker_ip = vm_data.worker_ip
    
    vm.updated_at = datetime.utcnow()
    vm.updated_by = vm_data.updated_by
    
    db.commit()
    db.refresh(vm)
    
    return vm


@router.delete("/{vm_id}", response_model=MessageResponse)
async def delete_vm(
    vm_id: int,
    deleted_by: Optional[int] = Query(None, description="ID del usuario que elimina"),
    delete_reason: Optional[str] = Query(None, description="Razón de eliminación"),
    db: Session = Depends(get_db)
):
    """
    Eliminar una VM (soft delete)
    """
    vm = db.query(VM).filter(
        VM.vm_id == vm_id,
        VM.deleted_at.is_(None)
    ).first()
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VM con ID {vm_id} no encontrada"
        )
    
    # Soft delete
    vm.deleted_at = datetime.utcnow()
    vm.deleted_by = deleted_by
    vm.delete_reason = delete_reason
    vm.status = 'deleted'
    
    db.commit()
    
    return MessageResponse(
        message=f"VM '{vm.name}' eliminada exitosamente",
        detail={"vm_id": vm_id, "name": vm.name}
    )
