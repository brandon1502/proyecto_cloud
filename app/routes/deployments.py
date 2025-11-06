# app/routes/deployments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import httpx

from app.db import get_db
from app.deps import login_required
from app.models import Template
from app.settings import settings   # <-- aquí estaba el error: usar app.settings

router = APIRouter(prefix="/deployments", tags=["deployments"])

class ForwardDeployRequest(BaseModel):
    template_id: int
    az_hint: Optional[str] = None     # "zone1" | "zone2" | ...
    slice_id: Optional[int] = None    # si ya creaste el slice en /slices

@router.post("/forward")
async def forward_json_to_friend(
    data: ForwardDeployRequest,
    db: Session = Depends(get_db),
    user = Depends(login_required),
):
    # 1) Cargar template del usuario
    tpl = (
        db.query(Template)
        .filter(
            Template.template_id == data.template_id,
            Template.user_id == user.user_id
        )
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    if not getattr(tpl, "json_template", None):
        raise HTTPException(status_code=409, detail="El template no tiene json_template guardado")

    # 2) Payload que reenvías a la API de tu amigo
    outgoing = {
        "zone": data.az_hint,
        "template_id": tpl.template_id,
        "template_name": tpl.name,
        "requested_by": {"user_id": int(user.user_id), "email": user.email},
        "slice_id": data.slice_id,
        "deployment": tpl.json_template,  # JSON guardado en DB
    }

    # 3) Enviar
    headers = {"Content-Type": "application/json"}
    # Si usas token:
    if getattr(settings, "FRIEND_DEPLOY_API_TOKEN", None):
        headers["Authorization"] = f"Bearer {settings.FRIEND_DEPLOY_API_TOKEN}"

    try:
        timeout = getattr(settings, "HTTP_CLIENT_TIMEOUT", 30)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                settings.FRIEND_DEPLOY_API_URL,  # definido en app.settings
                json=outgoing,
                headers=headers,
            )
        if resp.status_code // 100 != 2:
            raise HTTPException(
                status_code=502,
                detail=f"API de despliegue respondió {resp.status_code}: {resp.text}"
            )
        # si la API no devuelve JSON, evita .json() que lanzaría excepción
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return {"ok": True, "friend_status": resp.status_code, "friend_body": body}
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"No se pudo contactar a API de despliegue: {e}") 

class TriggerRequest(BaseModel):
    name: str
    zone_hint: str
    template_id: int
    topology: dict  # esto será tu json_template entero

@router.post("/trigger")
def trigger_deployment(
    body: TriggerRequest,
    user = Depends(login_required)
):
    """
    Este endpoint:
    - recibe del frontend los datos del despliegue
    - llama al servicio externo real (FRIEND_DEPLOY_API_URL)
    - retorna lo que respondió ese servicio
    """

    try:
        # lo que le mandas al "amigo" (worker de despliegue)
        payload_external = {
            "requester_user_id": user.user_id,    # quién pidió
            "name": body.name,
            "zone": body.zone_hint,
            "template_id": body.template_id,
            "topology": body.topology,            # <= el JSON enterito
        }

        headers = {
            "Content-Type": "application/json",
        }

        # si usas un token tipo API key/bearer interno:
        if settings.FRIEND_DEPLOY_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.FRIEND_DEPLOY_API_TOKEN}"

        resp = requests.post(
            settings.FRIEND_DEPLOY_API_URL,
            json=payload_external,
            headers=headers,
            timeout=settings.HTTP_CLIENT_TIMEOUT,
        )

        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"El motor de despliegue rechazó la solicitud: {resp.text}"
            )

        # devolvemos al frontend lo que dijo el motor,
        # ej: job_id, estado inicial, etc.
        return resp.json()

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Timeout hablando con motor de despliegue")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))