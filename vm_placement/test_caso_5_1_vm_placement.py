#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

PLACEMENT_URL = "http://localhost:5004/api/v1/placement"
NODES_URL = "http://localhost:5001/nodes/status"


def mostrar_hosts_y_zonas():
    print("=" * 70)
    print("1) LISTA DE HOSTS REGISTRADOS Y SUS ZONAS (/nodes/status)")
    print("=" * 70)

    r = requests.get(NODES_URL, timeout=5)
    r.raise_for_status()
    data = r.json()

    for node_id, node in data.items():
        print(f"{node['name']:25} | zone={node['zone']} | platform={node['platform']}")

    return data


def probar_placement_por_zona(zone="AZ1", platform="linux"):
    print("\n" + "=" * 70)
    print(f"2) SOLICITUD DE PLACEMENT PARA LA ZONA {zone}")
    print("=" * 70)

    payload = {
        "cpu": 1,
        "ram_gb": 1.0,
        "disk_gb": 1.0,
        "zone": zone,
        "platform": platform,
        "user_profile": "Estudiante",
        "technical_context": "Virtualizacion general"
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
    host = placement["host"]
    host_zone = placement["availability_zone"]

    print("\nComprobando coherencia de zona...")
    if host_zone == zone:
        print(f"[PASS] Host seleccionado: {host} (zone={host_zone}) coincide con la zona solicitada ({zone}).")
    else:
        print(f"[FAIL] Host seleccionado: {host} (zone={host_zone}) NO coincide con la zona solicitada ({zone}).")


if __name__ == "__main__":
    mostrar_hosts_y_zonas()
    probar_placement_por_zona(zone="AZ5", platform="openstack")
