# app/routes/vnc_proxy.py
"""
API endpoints para gestionar túneles VNC automáticos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx
import subprocess
import logging

from app.db import get_db
from app.deps import login_required

router = APIRouter(prefix="/vnc-proxy", tags=["vnc-proxy"])
logger = logging.getLogger(__name__)

# Almacenar procesos activos en memoria (en producción usar Redis)
active_tunnels = {}
active_proxies = {}


def get_ssh_port_from_worker_ip(worker_ip: str) -> int:
    """Determina el puerto SSH basado en la IP del worker"""
    if not worker_ip:
        return None
    
    last_octet = worker_ip.split('.')[-1]
    mapping = {'1': 5811, '2': 5812, '3': 5813}
    return mapping.get(last_octet)


@router.post("/start/{vm_id}")
async def start_vnc_proxy(
    vm_id: int,
    db: Session = Depends(get_db),
    user=Depends(login_required)
):
    """
    Inicia túnel SSH y websockify automáticamente para una VM
    Retorna la URL WebSocket para conectarse
    """
    try:
        # Obtener datos de la VM del Resources API
        async with httpx.AsyncClient(timeout=5.0) as client:
            vm_response = await client.get(f"http://10.20.12.26:8001/api/v1/vms/{vm_id}")
            if vm_response.status_code != 200:
                raise HTTPException(status_code=404, detail="VM no encontrada")
            
            vm = vm_response.json()
            
            # Obtener puerto VNC
            vnc_response = await client.get(f"http://10.20.12.26:8001/api/v1/vnc-ports/?vm_id={vm_id}")
            if vnc_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Puerto VNC no encontrado")
            
            vnc_ports = vnc_response.json()
            if not vnc_ports:
                raise HTTPException(status_code=404, detail="VM sin puerto VNC asignado")
            
            vnc_port = vnc_ports[0]['port_number']
            worker_ip = vm.get('worker_ip')
            
            if not worker_ip:
                raise HTTPException(status_code=400, detail="VM sin worker_ip configurado")
            
            ssh_port = get_ssh_port_from_worker_ip(worker_ip)
            if not ssh_port:
                raise HTTPException(status_code=400, detail="No se pudo determinar puerto SSH")
            
            # Puerto local único para este túnel
            local_vnc_port = 10000 + vm_id
            ws_port = 6000 + vm_id
            
            # 1. Crear túnel SSH (si no existe)
            if vm_id not in active_tunnels:
                ssh_cmd = [
                    'sshpass', '-p', 'ubuntu',  # Usar sshpass con contraseña
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'LogLevel=ERROR',
                    '-N',
                    '-L', f'{local_vnc_port}:localhost:{vnc_port}',
                    '-p', str(ssh_port),
                    'ubuntu@10.20.12.209'
                ]
                
                logger.info(f"🔧 Ejecutando SSH tunnel: {' '.join(ssh_cmd[4:])}")  # Sin mostrar contraseña
                
                tunnel = subprocess.Popen(
                    ssh_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL
                )
                active_tunnels[vm_id] = tunnel
                logger.info(f"✅ Túnel SSH creado para VM {vm_id}: localhost:{local_vnc_port} → 10.20.12.209:{ssh_port} → VNC:{vnc_port}")
                
                # Esperar a que se establezca el túnel
                import time
                time.sleep(3)
                
                # Verificar si el proceso sigue vivo
                if tunnel.poll() is not None:
                    stderr_output = tunnel.stderr.read().decode() if tunnel.stderr else "No stderr"
                    logger.error(f"❌ Túnel SSH falló inmediatamente: {stderr_output}")
                    del active_tunnels[vm_id]
                    raise HTTPException(status_code=500, detail=f"Túnel SSH falló: {stderr_output}")
            
            # 2. Crear websockify (si no existe)
            if vm_id not in active_proxies:
                ws_cmd = [
                    'websockify',
                    '--web', '/usr/share/novnc',
                    str(ws_port),
                    f'localhost:{local_vnc_port}'
                ]
                
                logger.info(f"🔧 Ejecutando websockify: {' '.join(ws_cmd)}")
                
                proxy = subprocess.Popen(
                    ws_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL
                )
                active_proxies[vm_id] = proxy
                logger.info(f"✅ WebSocket proxy creado para VM {vm_id} en puerto {ws_port}")
                
                # Verificar si el proceso sigue vivo
                import time
                time.sleep(1)
                if proxy.poll() is not None:
                    stderr_output = proxy.stderr.read().decode() if proxy.stderr else "No stderr"
                    logger.error(f"❌ Websockify falló inmediatamente: {stderr_output}")
                    del active_proxies[vm_id]
                    raise HTTPException(status_code=500, detail=f"Websockify falló: {stderr_output}")
            
            return {
                "success": True,
                "vm_id": vm_id,
                "vm_name": vm.get('name'),
                "websocket_url": f"ws://10.20.12.26:{ws_port}",
                "vnc_port": vnc_port,
                "worker_ip": worker_ip,
                "ssh_port": ssh_port
            }
            
    except Exception as e:
        logger.error(f"Error iniciando proxy VNC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop/{vm_id}")
async def stop_vnc_proxy(
    vm_id: int,
    user=Depends(login_required)
):
    """Detiene el túnel SSH y websockify de una VM"""
    stopped = []
    
    if vm_id in active_tunnels:
        active_tunnels[vm_id].terminate()
        del active_tunnels[vm_id]
        stopped.append("ssh_tunnel")
        logger.info(f"🛑 Túnel SSH detenido para VM {vm_id}")
    
    if vm_id in active_proxies:
        active_proxies[vm_id].terminate()
        del active_proxies[vm_id]
        stopped.append("websockify")
        logger.info(f"🛑 WebSocket proxy detenido para VM {vm_id}")
    
    return {
        "success": True,
        "vm_id": vm_id,
        "stopped": stopped
    }


@router.get("/status/{vm_id}")
async def get_proxy_status(
    vm_id: int,
    user=Depends(login_required)
):
    """Verifica si el proxy está activo para una VM"""
    return {
        "vm_id": vm_id,
        "tunnel_active": vm_id in active_tunnels,
        "proxy_active": vm_id in active_proxies,
        "websocket_port": 6000 + vm_id if vm_id in active_proxies else None
    }
