"""
Schemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ========== SLICE Schemas ==========
class SliceCreateRequest(BaseModel):
    """Request para crear un slice"""
    owner_id: int = Field(..., description="ID del usuario dueño")
    name: str = Field(..., max_length=150, description="Nombre del slice")
    az_id: Optional[int] = Field(None, description="ID de la zona de disponibilidad")
    template_id: Optional[int] = Field(None, description="ID de la plantilla usada")
    status: Optional[str] = Field("active", max_length=40, description="Estado del slice")
    placement_strategy: Optional[str] = Field(None, max_length=40)
    sla_overcommit_cpu_pct: Optional[Decimal] = Field(None, description="Porcentaje de overcommit de CPU")
    sla_overcommit_ram_pct: Optional[Decimal] = Field(None, description="Porcentaje de overcommit de RAM")
    internet_egress: Optional[bool] = Field(False, description="Acceso a internet")
    created_by: Optional[int] = Field(None, description="ID del usuario que crea")


class SliceUpdateRequest(BaseModel):
    """Request para actualizar un slice"""
    status: Optional[str] = Field(None, max_length=40, description="Nuevo estado")
    placement_strategy: Optional[str] = Field(None, max_length=40)
    sla_overcommit_cpu_pct: Optional[Decimal] = Field(None)
    sla_overcommit_ram_pct: Optional[Decimal] = Field(None)
    internet_egress: Optional[bool] = Field(None)
    updated_by: Optional[int] = Field(None, description="ID del usuario que actualiza")


class SliceResponse(BaseModel):
    """Schema de respuesta para slice"""
    slice_id: int
    owner_id: int
    name: str
    az_id: Optional[int] = None
    template_id: Optional[int] = None
    status: str
    placement_strategy: Optional[str] = None
    sla_overcommit_cpu_pct: Optional[Decimal] = None
    sla_overcommit_ram_pct: Optional[Decimal] = None
    internet_egress: bool
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== VLAN Schemas ==========
class VLANBase(BaseModel):
    """Schema base para VLAN"""
    vlan_number: int = Field(..., description="Número de VLAN (1-4094)")
    az_id: Optional[int] = Field(None, description="ID de la zona de disponibilidad")
    description: Optional[str] = Field(None, max_length=255)


class VLANResponse(VLANBase):
    """Schema de respuesta para VLAN"""
    vlan_id: int
    is_used: bool
    slice_id: Optional[int] = None
    reserved_at: Optional[datetime] = None
    reserved_by: Optional[int] = None
    released_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VLANReserveRequest(BaseModel):
    """Request para reservar una VLAN"""
    vlan_id: int = Field(..., description="ID de la VLAN a reservar")
    slice_id: Optional[int] = Field(None, description="ID del slice que reserva la VLAN")
    reserved_by: Optional[int] = Field(None, description="ID del usuario que reserva")
    description: Optional[str] = Field(None, max_length=255)


class VLANReleaseRequest(BaseModel):
    """Request para liberar una VLAN"""
    vlan_id: int = Field(..., description="ID de la VLAN a liberar")


# ========== VNC Port Schemas ==========
class VNCPortBase(BaseModel):
    """Schema base para puerto VNC"""
    port_number: int = Field(..., description="Número de puerto VNC")
    az_id: Optional[int] = Field(None, description="ID de la zona de disponibilidad")
    description: Optional[str] = Field(None, max_length=255)


class VNCPortResponse(VNCPortBase):
    """Schema de respuesta para puerto VNC"""
    vnc_port_id: int
    is_used: bool
    vm_id: Optional[int] = None
    slice_id: Optional[int] = None
    reserved_at: Optional[datetime] = None
    reserved_by: Optional[int] = None
    released_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VNCPortReserveRequest(BaseModel):
    """Request para reservar un puerto VNC"""
    vnc_port_id: int = Field(..., description="ID del puerto VNC a reservar")
    vm_id: Optional[int] = Field(None, description="ID de la VM que usa el puerto")
    slice_id: Optional[int] = Field(None, description="ID del slice")
    reserved_by: Optional[int] = Field(None, description="ID del usuario que reserva")
    description: Optional[str] = Field(None, max_length=255)


class VNCPortReleaseRequest(BaseModel):
    """Request para liberar un puerto VNC"""
    vnc_port_id: int = Field(..., description="ID del puerto VNC a liberar")


# ========== Generic Responses ==========
class MessageResponse(BaseModel):
    """Response genérico con mensaje"""
    message: str
    detail: Optional[dict] = None


# ========== VM Schemas ==========
class VMCreateRequest(BaseModel):
    """Request para crear una VM"""
    slice_id: int = Field(..., description="ID del slice al que pertenece")
    image_id: int = Field(..., description="ID de la imagen usada")
    name: str = Field(..., max_length=150, description="Nombre de la VM")
    vcpu: int = Field(..., ge=1, description="Número de vCPUs")
    ram_mb: int = Field(..., ge=1, description="RAM en MB")
    disk_gb: int = Field(..., ge=1, description="Disco en GB")
    az_id: Optional[int] = Field(None, description="ID de la zona de disponibilidad")
    status: Optional[str] = Field("running", max_length=40, description="Estado de la VM")
    worker_ip: Optional[str] = Field(None, max_length=45, description="IP del worker donde está la VM")
    created_by: Optional[int] = Field(None, description="ID del usuario que crea")


class VMUpdateRequest(BaseModel):
    """Request para actualizar una VM"""
    status: Optional[str] = Field(None, max_length=40, description="Nuevo estado")
    vcpu: Optional[int] = Field(None, ge=1)
    ram_mb: Optional[int] = Field(None, ge=1)
    disk_gb: Optional[int] = Field(None, ge=1)
    worker_ip: Optional[str] = Field(None, max_length=45, description="IP del worker")
    updated_by: Optional[int] = Field(None, description="ID del usuario que actualiza")


class VMResponse(BaseModel):
    """Schema de respuesta para VM"""
    vm_id: int
    slice_id: int
    az_id: Optional[int] = None
    image_id: int
    name: str
    vcpu: int
    ram_mb: int
    disk_gb: int
    status: str
    worker_ip: Optional[str] = None
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None
    
    class Config:
        from_attributes = True
