#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

PLACEMENT_URL = "http://localhost:5004/api/v1/placement"
NODES_URL = "http://localhost:5001/nodes/status"


def obtener_hosts():
    print("=" * 70)
    print("1) LISTA DE HOSTS REGISTRADOS (/nodes/status)")
    print("=" * 70)

    r = requests.get(NODES_URL, timeout=5)
    r.raise_for_status()
    data = r.json()

    for node_id, node in data.items():
        print(f"{node['name']:25} | zone={node['zone']} | platform={node['platform']}")

    return data


def pick_example_hosts(nodes_data):
    """Sigue sirviendo para escoger cualquier host OpenStack de ejemplo."""
    linux = None
    openstack = None

    for node_id, node in nodes_data.items():
        if node["platform"] == "linux" and linux is None:
            linux = {"id": node_id, "name": node["name"], "zone": node["zone"]}
        if node["platform"] == "openstack" and openstack is None:
            openstack = {"id": node_id, "name": node["name"], "zone": node["zone"]}
        if linux and openstack:
            break

    return linux, openstack


def pick_linux_in_zone(nodes_data, target_zone):
    """Devuelve un host linux especificamente en la zona target_zone."""
    for node_id, node in nodes_data.items():
        if node["platform"] == "linux" and node["zone"] == target_zone:
            return {"id": node_id, "name": node["name"], "zone": node["zone"]}
    return None


def test_backend(platform_expected, zone, nodes_data):
    print("\n" + "=" * 70)
    print(f"2) SOLICITUD DE PLACEMENT PARA BACKEND {platform_expected.upper()} EN ZONA {zone}")
    print("=" * 70)

    payload = {
        "cpu": 1,
        "ram_gb": 1.0,
        "disk_gb": 1.0,
        "zone": zone,
        "platform": platform_expected,
        "user_profile": "Estudiante",
        "technical_context": "Virtualizacion general",
    }

    print("JSON enviado a /api/v1/placement:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    resp = requests.post(PLACEMENT_URL, json=payload, timeout=10)
    print(f"\nCodigo HTTP: {resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        print("Respuesta no es JSON, FAIL automatico.")
        return

    print("\nJSON de respuesta:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    if not resp.ok or not data.get("success"):
        print("\n[FAIL] La API no devolvio un placement exitoso.")
        return

    placement = data["placement"]
    host_name = placement["host"]
    host_platform = placement["platform"]
    host_zone = placement["availability_zone"]

    # Buscar el host en nodes_status para comprobar su plataforma real
    real_platform = None
    for node in nodes_data.values():
        if node["name"] == host_name:
            real_platform = node["platform"]
            break

    print("\nComprobando coherencia de backend...")
    if host_platform == platform_expected and real_platform == platform_expected:
        print(f"[PASS] La API devolvio host {host_name} con platform={host_platform},")
        print(f"       y en nodes_status.json ese host tambien es {real_platform}.")
    else:
        print(f"[FAIL] Inconsistencia de backend. Se esperaba {platform_expected}.")
        print(f"       API platform={host_platform}, nodes_status={real_platform}.")

    print("\nComprobando coherencia de zona...")
    if host_zone == zone:
        print(f"[PASS] Host {host_name} pertenece a la zona solicitada ({zone}).")
    else:
        print(f"[FAIL] Host {host_name} pertenece a zona {host_zone}, no a {zone}.")


if __name__ == "__main__":
    # Paso 1: obtener hosts y mostrar plataformas
    nodes_data = obtener_hosts()

    # Elegir un host linux en AZ2 y un ejemplo OpenStack (cualquiera)
    linux_host_az2 = pick_linux_in_zone(nodes_data, "AZ2")
    _, openstack_host = pick_example_hosts(nodes_data)

    if linux_host_az2 is None or openstack_host is None:
        print("\n[ERROR] No se encontro host linux en AZ2 o ningun host openstack. Test abortado.")
    else:
        # Caso A: backend Linux en AZ2
        test_backend("linux", linux_host_az2["zone"], nodes_data)

        # Caso B: backend OpenStack en su zona (por ejemplo AZ4 o AZ5)
        test_backend("openstack", openstack_host["zone"], nodes_data)
