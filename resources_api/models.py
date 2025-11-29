"""
Modelos SQLAlchemy para Resources API
"""
from sqlalchemy import Column, BigInteger, Integer, String, TIMESTAMP, Boolean, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from .database import Base


class Slice(Base):
    """Modelo de Slice"""
    __tablename__ = "slices"
    
    slice_id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, nullable=False)
    az_id = Column(BigInteger, nullable=True)
    template_id = Column(BigInteger, nullable=True)
    name = Column(String(150), nullable=False)
    status = Column(String(40), default='active')
    placement_strategy = Column(String(40), nullable=True)
    sla_overcommit_cpu_pct = Column(DECIMAL(5, 2), nullable=True)
    sla_overcommit_ram_pct = Column(DECIMAL(5, 2), nullable=True)
    internet_egress = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    deleted_by = Column(BigInteger, nullable=True)
    delete_reason = Column(String(255), nullable=True)


class VLAN(Base):
    """Modelo de VLAN"""
    __tablename__ = "vlans"
    
    vlan_id = Column(BigInteger, primary_key=True, autoincrement=True)
    vlan_number = Column(Integer, nullable=False)
    az_id = Column(BigInteger, nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    slice_id = Column(BigInteger, nullable=True)
    description = Column(String(255), nullable=True)
    reserved_at = Column(TIMESTAMP, nullable=True)
    reserved_by = Column(BigInteger, nullable=True)
    released_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class VNCPort(Base):
    """Modelo de Puerto VNC"""
    __tablename__ = "vnc_ports"
    
    vnc_port_id = Column(BigInteger, primary_key=True, autoincrement=True)
    port_number = Column(Integer, nullable=False)
    az_id = Column(BigInteger, nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    vm_id = Column(BigInteger, nullable=True)
    slice_id = Column(BigInteger, nullable=True)
    description = Column(String(255), nullable=True)
    reserved_at = Column(TIMESTAMP, nullable=True)
    reserved_by = Column(BigInteger, nullable=True)
    released_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class VM(Base):
    """Modelo de VM"""
    __tablename__ = "vms"
    
    vm_id = Column(BigInteger, primary_key=True, autoincrement=True)
    slice_id = Column(BigInteger, nullable=False)
    az_id = Column(BigInteger, nullable=True)
    image_id = Column(BigInteger, nullable=False)
    name = Column(String(150), nullable=False)
    vcpu = Column(Integer, nullable=False)
    ram_mb = Column(Integer, nullable=False)
    disk_gb = Column(Integer, nullable=False)
    status = Column(String(40), default='stopped')
    worker_ip = Column(String(45), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    deleted_by = Column(BigInteger, nullable=True)
    delete_reason = Column(String(255), nullable=True)
