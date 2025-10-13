# app/routers/flavours.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Flavour
from app.deps import login_required
from typing import List
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter(prefix="/flavours", tags=["flavours"])

class FlavourResponse(BaseModel):
    flavour_id: int
    name: str
    vcpu: int
    ram_gb: float
    disk_gb: float
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[FlavourResponse])
def get_flavours(
    db: Session = Depends(get_db),
    user = Depends(login_required)
):
    """
    Obtiene todos los flavours disponibles
    """
    flavours = db.query(Flavour).all()
    
    # Convertir Decimal a float para la respuesta
    result = []
    for f in flavours:
        result.append({
            "flavour_id": f.flavour_id,
            "name": f.name,
            "vcpu": f.vcpu,
            "ram_gb": float(f.ram_gb),
            "disk_gb": float(f.disk_gb)
        })
    
    return result