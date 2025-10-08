from sqlalchemy import Column, BigInteger, Integer, String, Boolean, TIMESTAMP, JSON, Enum, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base
import enum

class TokenType(str, enum.Enum):
    session = "session"
    pat = "pat"
    service = "service"

class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    last_login_at = Column(TIMESTAMP, nullable=True)

    tokens = relationship("ApiToken", back_populates="user", cascade="all, delete-orphan")

class ApiToken(Base):
    __tablename__ = "api_tokens"
    token_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_type = Column(Enum(TokenType), nullable=False, default=TokenType.session)
    token_hash = Column(String(64), nullable=False, unique=True)
    scopes = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    expires_at = Column(TIMESTAMP, nullable=False)
    last_used_at = Column(TIMESTAMP, nullable=True, index=True)
    inactive_timeout_sec = Column(Integer, nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
    created_by_ip = Column(String(45), nullable=True)

    user = relationship("User", back_populates="tokens")

class AvailabilityZone(Base):
    __tablename__ = "availability_zones"
    az_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)

class Template(Base):
    __tablename__ = "templates"
    template_id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    az_id = Column(BigInteger, ForeignKey("availability_zones.az_id", ondelete="SET NULL"), nullable=True)
    name = Column(String(150), nullable=False)
    status = Column(String(40), nullable=True, default="draft")
    placement_strategy = Column(String(40), nullable=True)
    sla_overcommit_cpu_pct = Column(DECIMAL(5,2), nullable=True)
    sla_overcommit_ram_pct = Column(DECIMAL(5,2), nullable=True)
    internet_egress = Column(Boolean, nullable=True, default=False)
    created_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    deleted_by = Column(BigInteger, nullable=True)
    delete_reason = Column(String(255), nullable=True)
