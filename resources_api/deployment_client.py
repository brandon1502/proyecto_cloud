"""
Cliente Python para deployment de slices
Usar desde el servidor que hace el deployment (10.20.12.209)
"""
import requests
import json
from typing import Dict, List, Optional


class DeploymentClient:
    """Cliente para gestionar el deployment y guardar en BD"""
    
    def __init__(self, host="10.20.12.26", port=8001):
        self.base_url = f"http://{host}:{port}/api/v1"
    
    # ==================== SLICES ====================
    
    def create_slice(self, owner_id: int, name: str, **kwargs) -> Dict:
        """
        Crear un slice después de deployment exitoso
        
        Args:
            owner_id: ID del usuario dueño
            name: Nombre del slice
            **kwargs: Campos opcionales (az_id, template_id, status, etc.)
        
        Returns:
            Datos del slice creado
        """
        data = {
            "owner_id": owner_id,
            "name": name,
            **kwargs
        }
        response = requests.post(f"{self.base_url}/slices/", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_slice(self, slice_id: int) -> Dict:
        """Obtener información de un slice"""
        response = requests.get(f"{self.base_url}/slices/{slice_id}")
        response.raise_for_status()
        return response.json()
    
    def update_slice(self, slice_id: int, **kwargs) -> Dict:
        """
        Actualizar un slice
        
        Args:
            slice_id: ID del slice
            **kwargs: Campos a actualizar (status, updated_by, etc.)
        """
        response = requests.put(f"{self.base_url}/slices/{slice_id}", json=kwargs)
        response.raise_for_status()
        return response.json()
    
    def delete_slice(self, slice_id: int, deleted_by: Optional[int] = None, 
                     reason: Optional[str] = None) -> Dict:
        """Eliminar un slice (soft delete)"""
        params = {}
        if deleted_by:
            params['deleted_by'] = deleted_by
        if reason:
            params['delete_reason'] = reason
        
        response = requests.delete(f"{self.base_url}/slices/{slice_id}", params=params)
        response.raise_for_status()
        return response.json()
    
    def list_slices(self, owner_id: Optional[int] = None, 
                    status: Optional[str] = None) -> List[Dict]:
        """Listar slices con filtros"""
        params = {}
        if owner_id:
            params['owner_id'] = owner_id
        if status:
            params['status'] = status
        
        response = requests.get(f"{self.base_url}/slices/", params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== VLANS ====================
    
    def get_available_vlan(self, az_id: Optional[int] = None) -> Optional[Dict]:
        """Obtener una VLAN disponible"""
        params = {'limit': 1}
        if az_id:
            params['az_id'] = az_id
        
        response = requests.get(f"{self.base_url}/vlans/available", params=params)
        response.raise_for_status()
        vlans = response.json()
        return vlans[0] if vlans else None
    
    def reserve_vlan(self, vlan_id: int, slice_id: int, 
                     reserved_by: Optional[int] = None, 
                     description: Optional[str] = None) -> Dict:
        """Reservar una VLAN para un slice"""
        data = {
            "vlan_id": vlan_id,
            "slice_id": slice_id,
            "reserved_by": reserved_by,
            "description": description
        }
        response = requests.post(f"{self.base_url}/vlans/reserve", json=data)
        response.raise_for_status()
        return response.json()
    
    def release_vlan(self, vlan_id: int) -> Dict:
        """Liberar una VLAN"""
        response = requests.post(f"{self.base_url}/vlans/release", 
                                json={"vlan_id": vlan_id})
        response.raise_for_status()
        return response.json()
    
    # ==================== VNC PORTS ====================
    
    def get_available_vnc_ports(self, count: int = 1, 
                                az_id: Optional[int] = None) -> List[Dict]:
        """Obtener puertos VNC disponibles"""
        params = {'limit': count}
        if az_id:
            params['az_id'] = az_id
        
        response = requests.get(f"{self.base_url}/vnc-ports/available", params=params)
        response.raise_for_status()
        return response.json()
    
    def reserve_vnc_port(self, vnc_port_id: int, vm_id: int, 
                        slice_id: Optional[int] = None,
                        reserved_by: Optional[int] = None,
                        description: Optional[str] = None) -> Dict:
        """Reservar un puerto VNC para una VM"""
        data = {
            "vnc_port_id": vnc_port_id,
            "vm_id": vm_id,
            "slice_id": slice_id,
            "reserved_by": reserved_by,
            "description": description
        }
        response = requests.post(f"{self.base_url}/vnc-ports/reserve", json=data)
        response.raise_for_status()
        return response.json()
    
    def release_vnc_port(self, vnc_port_id: int) -> Dict:
        """Liberar un puerto VNC"""
        response = requests.post(f"{self.base_url}/vnc-ports/release",
                                json={"vnc_port_id": vnc_port_id})
        response.raise_for_status()
        return response.json()


# ==================== EJEMPLO DE USO ====================

def deploy_slice_workflow():
    """
    Flujo completo de deployment desde el servidor que despliega
    """
    client = DeploymentClient(host="10.20.12.26", port=8001)
    
    print("🚀 Iniciando deployment de slice...")
    
    # 1. Obtener recursos necesarios ANTES de desplegar
    print("\n📡 1. Obteniendo VLAN disponible...")
    vlan = client.get_available_vlan()
    if not vlan:
        print("❌ No hay VLANs disponibles!")
        return
    print(f"   ✅ VLAN {vlan['vlan_number']} disponible (ID: {vlan['vlan_id']})")
    
    print("\n🖥️  2. Obteniendo 3 puertos VNC...")
    vnc_ports = client.get_available_vnc_ports(count=3)
    if len(vnc_ports) < 3:
        print(f"❌ Solo hay {len(vnc_ports)} puertos VNC disponibles!")
        return
    print(f"   ✅ {len(vnc_ports)} puertos VNC disponibles")
    for port in vnc_ports:
        print(f"      - Puerto {port['port_number']} (ID: {port['vnc_port_id']})")
    
    # 2. HACER EL DEPLOYMENT EN OPENSTACK/OTRO SISTEMA
    print("\n⚙️  3. Desplegando en OpenStack...")
    print("   [Tu código de deployment aquí]")
    print("   - Crear VMs")
    print("   - Configurar red")
    print("   - Asignar IPs")
    print("   - etc...")
    
    # Simular que el deployment fue exitoso
    deployment_success = True
    
    if not deployment_success:
        print("❌ Deployment falló, no se guarda en BD")
        return
    
    print("   ✅ Deployment exitoso en OpenStack!")
    
    # 3. SOLO SI EL DEPLOYMENT FUE EXITOSO, guardar en BD
    print("\n💾 4. Guardando slice en base de datos...")
    slice_data = client.create_slice(
        owner_id=1,
        name="Slice de Producción Web",
        az_id=1,
        template_id=1,
        status="active",
        placement_strategy="distributed",
        sla_overcommit_cpu_pct=1.5,
        sla_overcommit_ram_pct=1.2,
        internet_egress=True,
        created_by=1
    )
    slice_id = slice_data['slice_id']
    print(f"   ✅ Slice guardado con ID: {slice_id}")
    print(f"   Nombre: {slice_data['name']}")
    print(f"   Estado: {slice_data['status']}")
    
    # 4. Reservar VLAN para el slice
    print(f"\n🔒 5. Reservando VLAN {vlan['vlan_number']} para slice...")
    client.reserve_vlan(
        vlan_id=vlan['vlan_id'],
        slice_id=slice_id,
        reserved_by=1,
        description=f"VLAN para slice {slice_id}"
    )
    print("   ✅ VLAN reservada")
    
    # 5. Reservar puertos VNC para cada VM
    print("\n🔒 6. Reservando puertos VNC para las VMs...")
    vm_ids = [101, 102, 103]  # IDs de las VMs creadas en OpenStack
    for vm_id, port in zip(vm_ids, vnc_ports):
        client.reserve_vnc_port(
            vnc_port_id=port['vnc_port_id'],
            vm_id=vm_id,
            slice_id=slice_id,
            reserved_by=1,
            description=f"Puerto VNC para VM {vm_id}"
        )
        print(f"   ✅ Puerto {port['port_number']} reservado para VM {vm_id}")
    
    # 6. Actualizar estado del slice
    print("\n🔄 7. Actualizando estado a 'running'...")
    client.update_slice(
        slice_id=slice_id,
        status="running",
        updated_by=1
    )
    print("   ✅ Estado actualizado")
    
    print("\n" + "="*50)
    print("✅ DEPLOYMENT COMPLETO")
    print("="*50)
    print(f"Slice ID: {slice_id}")
    print(f"VLAN: {vlan['vlan_number']}")
    print(f"VMs: {len(vm_ids)}")
    print(f"Estado: running")
    
    return slice_id


def cleanup_slice_workflow(slice_id: int):
    """
    Flujo de limpieza cuando se elimina un slice
    """
    client = DeploymentClient(host="10.20.12.26", port=8001)
    
    print(f"\n🧹 Limpiando slice {slice_id}...")
    
    # 1. Obtener información del slice
    slice_data = client.get_slice(slice_id)
    print(f"   Slice: {slice_data['name']}")
    
    # 2. Eliminar VMs en OpenStack (tu código aquí)
    print("   [Tu código para eliminar VMs en OpenStack]")
    
    # 3. Liberar recursos
    print("\n🔓 Liberando recursos...")
    
    # Aquí deberías consultar qué VLAN y puertos VNC están asociados al slice
    # y liberarlos uno por uno
    
    # 4. Marcar slice como eliminado en BD
    print("\n🗑️  Marcando slice como eliminado...")
    client.delete_slice(
        slice_id=slice_id,
        deleted_by=1,
        reason="Solicitado por usuario"
    )
    print("   ✅ Slice eliminado")


if __name__ == "__main__":
    # Ejecutar el flujo de deployment
    slice_id = deploy_slice_workflow()
    
    # Si quieres probar la limpieza, descomenta:
    # if slice_id:
    #     cleanup_slice_workflow(slice_id)
