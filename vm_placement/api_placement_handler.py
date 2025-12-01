#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Handler para el módulo de VM Placement PUCP
Recibe solicitudes JSON, consulta workers disponibles y ejecuta placement
"""

from flask import Flask, request, jsonify
from typing import Dict, List, Optional
import requests
from dataclasses import asdict

# Importar las clases del módulo de placement
from vm_placement import (
    SliceRequest, HostState, PlacementDecision,
    decide_vm_placement
)

app = Flask(__name__)

# ========================================
# CONFIGURACIÓN DE APIs EXTERNAS
# ========================================

# URL base para consultar estado de workers
# Ajusta según tu infraestructura real
# AJUSTAR HARDCODED
#WORKER_API_BASE = "http://localhost:8081/api/v1"

# Endpoints específicos
#WORKERS_ENDPOINT = f"{WORKER_API_BASE}/workers"  # GET: lista todos los workers
#WORKER_DETAIL_ENDPOINT = f"{WORKER_API_BASE}/workers/{{worker_id}}"  # GET: detalle de un worker


# API de Monitoreo
MONITORING_API = "http://localhost:5001"   # donde corre tu metrics_api

NODES_STATUS_ENDPOINT = f"{MONITORING_API}/nodes/status"



# ========================================
# FUNCIONES AUXILIARES
# ========================================

def parse_slice_request(json_data: Dict) -> Optional[SliceRequest]:
    """
    Convierte el JSON recibido en un objeto SliceRequest
    
    Formato esperado del JSON:
    {
        "cpu": 4,
        "ram_gb": 8.0,
        "disk_gb": 50.0,
        "zone": "AZ1",
        "platform": "linux",
        "user_profile": "Estudiante", 
        "technical_context": "Cloud / Web / Dev", 
    }
    """
    try:
        # Validar campos requeridos
        required_fields = ["cpu", "ram_gb", "disk_gb", "zone"]
        for field in required_fields:
            if field not in json_data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Crear objeto SliceRequest con valores del JSON
        slice_req = SliceRequest(
            cpu=int(json_data["cpu"]),
            ram_gb=float(json_data["ram_gb"]),
            disk_gb=float(json_data["disk_gb"]),
            zone=json_data["zone"],
            platform=json_data.get("platform"),
            user_profile=json_data.get("user_profile"),
            technical_context=json_data.get("technical_context"),
        )
        
        return slice_req
    
    except (ValueError, KeyError, TypeError) as e:
        print(f"❌ Error parseando SliceRequest: {e}")
        return None



def fetch_workers_in_zone(zone: str) -> List[Dict]:

    import requests
    
    try:
        response = requests.get(NODES_STATUS_ENDPOINT, timeout=3)
        if response.status_code != 200:
            print("❌ Error obteniendo nodes_status.json")
            return []

        nodes = response.json()

        # Filtrar por zona
        zone_nodes = [
            node_data for node_data in nodes.values()
            if node_data["zone"] == zone
        ]

        return zone_nodes

    except Exception as e:
        print(f"❌ Error consultando nodos: {e}")
        return []

def parse_worker_to_hoststate(worker_data: Dict) -> Optional[HostState]:
    """
    Convierte un nodo de nodes_status.json al objeto HostState.
    Compatible con el NUEVO formato con unidades.
    """

    try:
        # ============================
        # 1. Extraer capacidades
        # ============================
        cpu_capacity = worker_data["cpu_capacity"]["value"]        # cores
        ram_capacity = worker_data["ram_capacity"]["value"]        # GiB
        disk_capacity = worker_data["disk_capacity"]["value"]      # GB

        # ============================
        # 2. Extraer uso actual
        # ============================
        cpu_stats = worker_data["current_usage"]["cpu"]
        ram_stats = worker_data["current_usage"]["ram"]
        disk_used = worker_data["current_usage"]["disk"]["used"]

        # ============================
        # 3. Crear HostState
        # ============================
        host = HostState(
            name=worker_data.get("name", worker_data["id"]),
            platform=worker_data["platform"],
            zone=worker_data["zone"],

            cpu_capacity=float(cpu_capacity),
            ram_gb_capacity=float(ram_capacity),
            disk_gb_capacity=float(disk_capacity),

            mu_cpu=float(cpu_stats["mean"]*cpu_capacity/100.0),
            sigma_cpu=float(cpu_stats["std"]*cpu_capacity/100.0),
            mu_ram_gb=float(ram_stats["mean"]),
            sigma_ram_gb=float(ram_stats["std"]),
            disk_gb_used=float(disk_used),

            enabled=worker_data.get("enabled", True),
            in_maintenance=worker_data.get("in_maintenance", False),
            metadata=worker_data.get("metadata", {})
        )

        return host

    except Exception as e:
        print(f"❌ Error parseando nodo a HostState: {e}")
        return None



def get_hosts_for_zone(zone: str) -> List[HostState]:
    """
    Obtiene todos los hosts disponibles en una zona específica
    
    1. Consulta la lista de workers en la zona
    2. Para cada worker, obtiene sus detalles completos
    3. Convierte cada worker a HostState
    """
    print(f"\n🔍 Consultando workers en zona: {zone}")
    
    # Obtener lista de workers en la zona
    workers_basic = fetch_workers_in_zone(zone)
    
    if not workers_basic:
        print(f"⚠️ No se encontraron workers en la zona {zone}")
        return []
    
    print(f"✓ Encontrados {len(workers_basic)} workers en zona {zone}")
    
    # Obtener detalles de cada worker y convertir a HostState
    hosts = []
    
    for worker_basic in workers_basic:
        worker_id = worker_basic.get("id") or worker_basic.get("name")
        
        if not worker_id:
            print(f"⚠️ Worker sin ID, saltando...")
            continue
        
        # Convertir a HostState
        host = parse_worker_to_hoststate(worker_basic)
        
        if host:
            hosts.append(host)
            print(f"  ✓ {host.name} ({host.platform}) - CPU: {host.cpu_capacity}, RAM: {host.ram_gb_capacity}GB")
        else:
            print(f"  ❌ No se pudo parsear worker {worker_id}")
    
    print(f"\n✓ Total de hosts válidos: {len(hosts)}")
    return hosts


# ========================================
# ENDPOINT PRINCIPAL DE LA API
# ========================================

@app.route('/api/v1/placement', methods=['POST'])
def placement_endpoint():
    """
    Endpoint principal que recibe solicitud de placement y retorna decisión
    
    Request JSON:
    {
        "cpu": 4,
        "ram_gb": 8.0,
        "disk_gb": 50.0,
        "zone": "AZ1",
        "platform": "linux",
        "user_profile": "Estudiante",
        "technical_context": "Cloud / Web / Dev",
    }
    
    Response JSON (éxito):
    {
        "success": true,
        "placement": {
            "host": "compute-node-1",
            "platform": "linux",
            "availability_zone": "AZ1",
            "reason": "Host Linux seleccionado con riesgo máximo 0.0045"
        }
    }
    
    Response JSON (fallo):
    {
        "success": false,
        "error": "No hay hosts disponibles que cumplan los requisitos"
    }
    """
    
    print("\n" + "="*70)
    print("NUEVA SOLICITUD DE PLACEMENT")
    print("="*70)
    
    try:
        # 1. Parsear el JSON recibido
        json_data = request.get_json()
        
        if not json_data:
            return jsonify({
                "success": False,
                "error": "No se recibió JSON válido en el body"
            }), 400
        
        print(f"📥 Solicitud recibida: {json_data}")
        
        # 2. Convertir a SliceRequest
        slice_req = parse_slice_request(json_data)
        
        if not slice_req:
            return jsonify({
                "success": False,
                "error": "Error parseando los parámetros de la solicitud"
            }), 400
        
        print(f"\n✓ SliceRequest creado:")
        print(f"  - CPU: {slice_req.cpu} cores")
        print(f"  - RAM: {slice_req.ram_gb} GB")
        print(f"  - Disco: {slice_req.disk_gb} GB")
        print(f"  - Zona: {slice_req.zone}")
        print(f"  - Plataforma: {slice_req.platform or 'auto'}")
        print(f"  - Perfil: {slice_req.user_profile}")
        print(f"  - Contexto: {slice_req.technical_context}")
        
        # 3. Obtener hosts disponibles en la zona solicitada
        hosts = get_hosts_for_zone(slice_req.zone)
        
        if not hosts:
            return jsonify({
                "success": False,
                "error": f"No hay workers disponibles en la zona {slice_req.zone}"
            }), 404
        
        # 4. Ejecutar algoritmo de placement
        print(f"\n🎯 Ejecutando algoritmo de placement...")
        decision = decide_vm_placement(slice_req, hosts)
        
        # 5. Retornar resultado
        if decision:
            print(f"\n✅ PLACEMENT EXITOSO")
            print(f"  Host seleccionado: {decision.host}")
            print(f"  Plataforma: {decision.platform}")
            print(f"  Zona: {decision.availability_zone}")
            print(f"  Razón: {decision.reason}")
            
            return jsonify({
                "success": True,
                "placement": asdict(decision)
            }), 200
        
        else:
            print(f"\n❌ NO SE ENCONTRÓ HOST VIABLE")
            return jsonify({
                "success": False,
                "error": "No hay hosts disponibles que cumplan los requisitos de riesgo"
            }), 409
    
    except Exception as e:
        print(f"\n❌ ERROR INTERNO: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Endpoint simple para verificar que la API está funcionando"""
    return jsonify({
        "status": "healthy",
        "service": "VM Placement API",
        "version": "1.0"
    }), 200


# ========================================
# EJECUCIÓN DEL SERVIDOR
# ========================================

if __name__ == '__main__':
    print("="*70)
    print("SERVIDOR DE VM PLACEMENT API")
    print("="*70)
    print("Endpoints disponibles:")
    print("  POST /api/v1/placement  - Solicitar placement de VM")
    print("  GET  /api/v1/health     - Health check")
    print("="*70)
    print("\n🚀 Iniciando servidor en http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=5004,
        debug=True
    )