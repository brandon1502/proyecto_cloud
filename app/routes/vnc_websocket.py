# app/routes/vnc_websocket.py
"""
Proxy WebSocket para VNC - conecta el navegador con websockify en los servers
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import asyncio
import httpx
import logging

from app.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


def get_server_info(worker_ip: str):
    """Mapea worker_ip a server IP y puerto SSH (via gateway)"""
    mapping = {
        '192.168.201.1': {'server_id': 1, 'ssh_port': 5811, 'internal_ip': '10.20.201.1'},
        '192.168.201.2': {'server_id': 2, 'ssh_port': 5812, 'internal_ip': '10.20.201.2'},
        '192.168.201.3': {'server_id': 3, 'ssh_port': 5813, 'internal_ip': '10.20.201.3'},
    }
    return mapping.get(worker_ip)


@router.websocket("/ws/vnc/{vm_id}")
async def vnc_websocket_proxy(websocket: WebSocket, vm_id: int):
    """
    Proxy WebSocket que conecta el navegador con websockify en el server via SSH tunnel
    """
    logger.info(f"🔌 Iniciando proxy WebSocket para VM {vm_id}")
    await websocket.accept()
    logger.info(f"✅ WebSocket aceptado para VM {vm_id}")
    
    import subprocess
    import socket
    import random
    
    ssh_process = None
    sock = None
    
    try:
        # Obtener datos de la VM
        logger.info(f"📡 Consultando datos de VM {vm_id}...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Obtener VM info
            vm_response = await client.get(f"http://resources_api:8001/api/v1/vms/{vm_id}")
            logger.info(f"📊 Respuesta VM: status={vm_response.status_code}")
            if vm_response.status_code != 200:
                logger.error(f"❌ VM {vm_id} no encontrada")
                await websocket.close(code=1008, reason="VM no encontrada")
                return
            
            vm_data = vm_response.json()
            worker_ip = vm_data.get('worker_ip')
            logger.info(f"🖥️  Worker IP: {worker_ip}")
            
            # Obtener puerto VNC
            vnc_response = await client.get(f"http://resources_api:8001/api/v1/vnc-ports/?vm_id={vm_id}")
            logger.info(f"📊 Respuesta VNC port: status={vnc_response.status_code}")
            if vnc_response.status_code != 200:
                logger.error(f"❌ Puerto VNC no encontrado para VM {vm_id}")
                await websocket.close(code=1008, reason="Puerto VNC no encontrado")
                return
            
            ports = vnc_response.json()
            if not ports or len(ports) == 0:
                logger.error(f"❌ VM {vm_id} sin puerto VNC asignado")
                await websocket.close(code=1008, reason="VM sin puerto VNC asignado")
                return
            
            vnc_port = ports[0].get('port_number')
            logger.info(f"🔌 Puerto VNC: {vnc_port}")
            
        # Calcular puerto WebSocket remoto
        ws_port_remote = 6000 + (vnc_port - 5900)
        
        # Puerto local aleatorio para el túnel SSH
        local_port = random.randint(10000, 20000)
        
        # Obtener info del server
        server_info = get_server_info(worker_ip)
        if not server_info:
            await websocket.close(code=1008, reason=f"Worker IP no reconocido: {worker_ip}")
            return
        
        gateway_ip = '10.20.12.209'
        ssh_port = server_info['ssh_port']
        ssh_password = 'ubuntu'  # TODO: Usar variable de entorno
        
        logger.info(f"🔐 Creando túnel SSH: localhost:{local_port} -> {gateway_ip}:{ssh_port} -> websockify:{ws_port_remote}")
        
        # Crear túnel SSH con port forwarding
        # -L local_port:localhost:ws_port_remote = forward del puerto local al remoto
        ssh_cmd = [
            'sshpass', '-p', ssh_password,
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ServerAliveInterval=60',
            '-N',  # No ejecutar comando remoto
            '-L', f'{local_port}:localhost:{ws_port_remote}',
            '-p', str(ssh_port),
            f'ubuntu@{gateway_ip}'
        ]
        
        ssh_process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar a que el túnel esté listo
        await asyncio.sleep(2)
        
        if ssh_process.poll() is not None:
            logger.error(f"❌ Túnel SSH falló inmediatamente")
            await websocket.close(code=1011, reason="No se pudo crear túnel SSH")
            return
        
        logger.info(f"✅ Túnel SSH creado, conectando a localhost:{local_port}")
        
        # Conectar al puerto local del túnel
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect(('localhost', local_port))
            sock.setblocking(False)
            logger.info(f"✅ Conectado a websockify via túnel SSH")
        except Exception as e:
            logger.error(f"❌ No se pudo conectar al túnel: {e}")
            if ssh_process:
                ssh_process.terminate()
            await websocket.close(code=1011, reason=f"No se pudo conectar: {e}")
            return
        
        # Crear tareas para forward bidireccional
        async def forward_to_server():
            """Lee del navegador y envía al server"""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await asyncio.get_event_loop().sock_sendall(sock, data)
            except WebSocketDisconnect:
                logger.info("Cliente desconectado")
            except Exception as e:
                logger.error(f"Error forward to server: {e}")
            finally:
                sock.close()
        
        async def forward_to_client():
            """Lee del server y envía al navegador"""
            try:
                loop = asyncio.get_event_loop()
                while True:
                    data = await loop.sock_recv(sock, 4096)
                    if not data:
                        break
                    await websocket.send_bytes(data)
            except Exception as e:
                logger.error(f"Error forward to client: {e}")
            finally:
                await websocket.close()
        
        # Ejecutar ambas tareas en paralelo
        await asyncio.gather(
            forward_to_server(),
            forward_to_client(),
            return_exceptions=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error en proxy WebSocket: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        # Limpiar recursos
        if sock:
            try:
                sock.close()
            except:
                pass
        if ssh_process:
            try:
                ssh_process.terminate()
                ssh_process.wait(timeout=2)
                logger.info("🔒 Túnel SSH cerrado")
            except:
                try:
                    ssh_process.kill()
                except:
                    pass
