# app/routes/deployments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from app.db import get_db
from app.deps import login_required
from app.models import Template

router = APIRouter(prefix="/deployments", tags=["deployments"])

class TriggerRequest(BaseModel):
    name: str
    zone_hint: str
    template_id: int

@router.post("/trigger")
async def trigger_deployment(
    body: TriggerRequest,
    user = Depends(login_required),
    db: Session = Depends(get_db)
):
    """
    Este endpoint:
    - obtiene el json_template de la base de datos
    - lo envía al servidor de despliegue en http://10.20.12.209:8581/deploy
    - retorna lo que respondió ese servicio
    """
    
    # 1. Obtener el template de la base de datos
    tpl = (
        db.query(Template)
        .filter(
            Template.template_id == body.template_id,
            Template.user_id == user.user_id
        )
        .first()
    )
    
    if not tpl:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    if not tpl.json_template:
        raise HTTPException(
            status_code=409, 
            detail="El template no tiene json_template guardado"
        )

    # 2. Preparar el payload con el json_template de la BD
    # El servidor de despliegue espera topologia, recursos y subred al nivel raíz
    payload_external = {
        "requester_user_id": user.user_id,
        "requester_username": user.email,  # usar email ya que no hay username
        "requester_email": user.email,
        "name": body.name,
        "zone": body.zone_hint,
        "template_id": body.template_id,
        # Expandir el json_template al nivel raíz
        **tpl.json_template,  # Esto pone topologia, recursos, subred al mismo nivel
    }

    # 3. Enviar al servidor de despliegue
    DEPLOY_API_URL = "http://10.20.12.209:8581/deploy"
    
    headers = {
        "Content-Type": "application/json",
    }

    try:
        timeout = 30
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                DEPLOY_API_URL,
                json=payload_external,
                headers=headers,
            )

        if resp.status_code >= 400:
            error_detail = resp.text
            try:
                error_json = resp.json()
                error_detail = error_json.get("detail", error_json.get("error", resp.text))
            except:
                pass
            
            raise HTTPException(
                status_code=502,
                detail=f"Error en servidor de despliegue: {error_detail}"
            )

        # Devolver la respuesta del servidor de despliegue
        try:
            result = resp.json()
            return {
                "success": True,
                "worker_job_id": result.get("job_id", result.get("deployment_id", None)),
                "status": result.get("status", "ACCEPTED"),
                "message": result.get("message", "Despliegue enviado correctamente"),
                "details": result
            }
        except:
            return {
                "success": True,
                "status": "ACCEPTED",
                "message": "Despliegue enviado correctamente",
                "response_text": resp.text
            }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout: El servidor de despliegue no respondió a tiempo"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo conectar con el servidor de despliegue: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )