"""Modelos de la base de datos (SQLAlchemy).

Contiene las tablas principales utilizadas por la aplicación:
- Roles, Users, ApiToken
- Templates, TemplateVM, TemplateEdge
- Flavours, AvailabilityZone, Slice

Las relaciones y constraints están definidas en las clases; los scripts
de inicialización se encuentran en `db/init/`.
"""

from sqlalchemy import (
    Column, BigInteger, Integer, String, Boolean, TIMESTAMP, JSON, Enum,
    ForeignKey, DECIMAL, UniqueConstraint, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import enum


# ------------------------
# Enums
# ------------------------
class TokenType(str, enum.Enum):
    session = "session"
    pat = "pat"
    service = "service"


# ------------------------
# Roles
# ------------------------
class Role(Base):
    __tablename__ = "roles"
    role_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)


# ------------------------
# Users
# ------------------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # FK a roles.role_id (default 2 a nivel BD recomendado; aquí lo dejamos explícito)
    role_id = Column(
        BigInteger,
        ForeignKey("roles.role_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        server_default=text("2"),
    )

    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    last_login_at = Column(TIMESTAMP, nullable=True)

    role = relationship("Role", lazy="joined")
    tokens = relationship("ApiToken", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="owner", cascade="all, delete-orphan")


# ------------------------
# API Tokens
# ------------------------
class ApiToken(Base):
    __tablename__ = "api_tokens"

    token_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_type = Column(Enum(TokenType), nullable=False, server_default=TokenType.session.value)
    token_hash = Column(String(64), nullable=False, unique=True)
    scopes = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    expires_at = Column(TIMESTAMP, nullable=False)
    last_used_at = Column(TIMESTAMP, nullable=True, index=True)
    inactive_timeout_sec = Column(Integer, nullable=True)
    revoked = Column(Boolean, nullable=False, server_default=text("0"))
    created_by_ip = Column(String(45), nullable=True)

    user = relationship("User", back_populates="tokens")

# ------------------------
# Templates (usa user_id)
# ------------------------
class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_templates_owner_name"),
    )

    template_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    name = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)

    created_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    updated_last_at = Column(TIMESTAMP, nullable=True)

    # 👇 NUEVO: guarda el JSON generado
    json_template = Column(JSON, nullable=True)
    owner = relationship("User", back_populates="templates")
    vms = relationship("TemplateVM", back_populates="template", cascade="all, delete-orphan")
    edges = relationship("TemplateEdge", back_populates="template", cascade="all, delete-orphan")
    slices = relationship("Slice", back_populates="template", cascade="all, delete-orphan")


# ------------------------
# Slices
# ------------------------
class Slice(Base):
    __tablename__ = "slices"

    slice_id = Column(BigInteger, primary_key=True, autoincrement=True)

    owner_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    az_id = Column(BigInteger, ForeignKey("availability_zones.az_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    template_id = Column(BigInteger, ForeignKey("templates.template_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)

    name = Column(String(150), nullable=False)
    status = Column(String(40), nullable=True, server_default=text("'active'"))

    placement_strategy = Column(String(40), nullable=True)
    sla_overcommit_cpu_pct = Column(DECIMAL(5, 2), nullable=True)
    sla_overcommit_ram_pct = Column(DECIMAL(5, 2), nullable=True)
    # Si no quieres default 0, envía None explícito al crear.
    internet_egress = Column(Boolean, nullable=True, server_default=text("0"))

    created_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    created_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    deleted_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    delete_reason = Column(String(255), nullable=True)

    # relaciones
    availability_zone = relationship("AvailabilityZone", back_populates="slices")
    template = relationship("Template", back_populates="slices")   # 👈 coincide con Template.slices


# ------------------------
# Template VMs (ram_gb, imagen, public_access)
# ------------------------

# ------------------------
# Template Edges
# ------------------------
class TemplateEdge(Base):
    __tablename__ = "template_edges"
    __table_args__ = (
        UniqueConstraint("template_id", "from_vm_id", "to_vm_id", name="uq_tpl_edge"),
    )

    template_edge_id = Column(BigInteger, primary_key=True, autoincrement=True)
    template_id = Column(BigInteger, ForeignKey("templates.template_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    from_vm_id = Column(BigInteger, ForeignKey("template_vms.template_vm_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    to_vm_id = Column(BigInteger, ForeignKey("template_vms.template_vm_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    template = relationship("Template", back_populates="edges")
    from_vm = relationship("TemplateVM", foreign_keys=[from_vm_id], back_populates="edges_from")
    to_vm = relationship("TemplateVM", foreign_keys=[to_vm_id], back_populates="edges_to")


# Agregar al archivo models.py después de los enums y antes de Template

# ------------------------
# Flavours
# ------------------------
class Flavour(Base):
    __tablename__ = "flavours"
    
    flavour_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    vcpu = Column(Integer, nullable=False)
    ram_gb = Column(DECIMAL(5, 2), nullable=False)
    disk_gb = Column(DECIMAL(5, 2), nullable=False)
    
    # Relación con template_vms
    template_vms = relationship("TemplateVM", back_populates="flavour")


# ------------------------
# Template VMs (ACTUALIZADO con FK a flavours)
# ------------------------
class TemplateVM(Base):
    __tablename__ = "template_vms"
    __table_args__ = (
        UniqueConstraint("template_id", "name", name="uq_tpl_vm_name"),
    )

    template_vm_id = Column(BigInteger, primary_key=True, autoincrement=True)
    template_id = Column(BigInteger, ForeignKey("templates.template_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    flavour_id = Column(BigInteger, ForeignKey("flavours.flavour_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    
    name = Column(String(150), nullable=False)
    imagen = Column(String(40), nullable=True)
    public_access = Column(Boolean, nullable=False, server_default=text("0"))

    template = relationship("Template", back_populates="vms")
    flavour = relationship("Flavour", back_populates="template_vms")

    edges_from = relationship("TemplateEdge",
                              foreign_keys="TemplateEdge.from_vm_id",
                              back_populates="from_vm",
                              cascade="all, delete-orphan")
    edges_to = relationship("TemplateEdge",
                            foreign_keys="TemplateEdge.to_vm_id",
                            back_populates="to_vm",
                            cascade="all, delete-orphan")
    
# app/models.py (añade al final)

class AvailabilityZone(Base):
    __tablename__ = "availability_zones"
    az_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    provider = Column(String(120), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    created_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    deleted_by = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    delete_reason = Column(String(255), nullable=True)

    slices = relationship("Slice", back_populates="availability_zone")

