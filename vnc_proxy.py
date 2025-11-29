#!/usr/bin/env python3
"""
VNC Proxy Service - Crea túneles SSH automáticos y websockify para acceso VNC desde navegador
"""

import subprocess
import time
import signal
import sys
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VNCProxyManager:
    def __init__(self):
        self.tunnels: Dict[int, subprocess.Popen] = {}
        self.proxies: Dict[int, subprocess.Popen] = {}
        
    def get_ssh_port(self, worker_ip: str) -> Optional[int]:
        """Determina el puerto SSH basado en la IP del worker"""
        if not worker_ip:
            return None
        
        last_octet = worker_ip.split('.')[-1]
        mapping = {'1': 5811, '2': 5812, '3': 5813}
        return mapping.get(last_octet)
    
    def create_tunnel(self, vm_id: int, vnc_port: int, worker_ip: str) -> bool:
        """Crea túnel SSH para acceso VNC"""
        ssh_port = self.get_ssh_port(worker_ip)
        if not ssh_port:
            logger.error(f"No se pudo determinar puerto SSH para {worker_ip}")
            return False
        
        # Puerto local único para este túnel
        local_port = 10000 + vm_id
        
        # Crear túnel SSH
        ssh_cmd = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-N',
            '-L', f'{local_port}:localhost:{vnc_port}',
            '-p', str(ssh_port),
            'ubuntu@10.20.12.209'
        ]
        
        try:
            tunnel = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.tunnels[vm_id] = tunnel
            logger.info(f"✅ Túnel SSH creado: VM {vm_id} -> localhost:{local_port}")
            time.sleep(2)  # Esperar a que se establezca
            return True
        except Exception as e:
            logger.error(f"❌ Error creando túnel SSH: {e}")
            return False
    
    def create_websockify(self, vm_id: int) -> bool:
        """Crea websockify para convertir VNC a WebSocket"""
        local_vnc_port = 10000 + vm_id
        ws_port = 6000 + vm_id  # Puerto WebSocket
        
        # Iniciar websockify
        ws_cmd = [
            'websockify',
            '--web=/usr/share/novnc',
            f'{ws_port}',
            f'localhost:{local_vnc_port}'
        ]
        
        try:
            proxy = subprocess.Popen(ws_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.proxies[vm_id] = proxy
            logger.info(f"✅ WebSocket proxy creado: VM {vm_id} -> ws://localhost:{ws_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creando websockify: {e}")
            return False
    
    def stop_tunnel(self, vm_id: int):
        """Detiene túnel SSH y websockify de una VM"""
        if vm_id in self.tunnels:
            self.tunnels[vm_id].terminate()
            del self.tunnels[vm_id]
            logger.info(f"🛑 Túnel SSH detenido: VM {vm_id}")
        
        if vm_id in self.proxies:
            self.proxies[vm_id].terminate()
            del self.proxies[vm_id]
            logger.info(f"🛑 WebSocket proxy detenido: VM {vm_id}")
    
    def stop_all(self):
        """Detiene todos los túneles y proxies"""
        for vm_id in list(self.tunnels.keys()):
            self.stop_tunnel(vm_id)
        logger.info("🛑 Todos los servicios detenidos")


if __name__ == '__main__':
    manager = VNCProxyManager()
    
    def signal_handler(sig, frame):
        logger.info("\n🛑 Deteniendo servicios...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 VNC Proxy Manager iniciado")
    logger.info("Presiona Ctrl+C para detener")
    
    # Mantener el script corriendo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
