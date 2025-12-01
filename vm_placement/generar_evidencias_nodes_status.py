#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime
from deepdiff import DeepDiff  # pip install deepdiff

NODES_URL = "http://localhost:5001/nodes/status"
PLACEMENT_URL = "http://localhost:5004/api/v1/placement"

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_text(text, path):
    with open(path, "w") as f:
        f.write(text)

def get_nodes_status():
    resp = requests.get(NODES_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

def run_placement():
    payload = {
        "cpu": 64,
        "ram_gb": 1.0,
        "disk_gb": 1.0,
        "zone": "AZ4",
        "platform": "openstack",
        "user_profile": "Estudiante",
        "technical_context": "Virtualizacion general"
    }

    print("\n--- Enviando solicitud a VM Placement ---")
    print(json.dumps(payload, indent=2))

    resp = requests.post(PLACEMENT_URL, json=payload, timeout=10)

    print("\n--- Respuesta de VM Placement ---")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2))
    except:
        print(resp.text)

    return resp.status_code, resp.text

if __name__ == "__main__":

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_dir = f"evidencias/nodes_status_{ts}"
    os.makedirs(base_dir, exist_ok=True)

    print("\n===============================================================")
    print(" GET /nodes/status (antes)")
    print("===============================================================")

    before = get_nodes_status()
    save_json(before, f"{base_dir}/nodes_status_BEFORE.json")
    print(json.dumps(before, indent=2))

    print("\n===============================================================")
    print(" EJECUTANDO ACCION DE PRUEBA (placement)")
    print("===============================================================")

    status_code, placement_resp = run_placement()
    save_text(placement_resp, f"{base_dir}/placement_response.txt")

    print("\n===============================================================")
    print(" GET /nodes/status (despues)")
    print("===============================================================")

    after = get_nodes_status()
    save_json(after, f"{base_dir}/nodes_status_AFTER.json")
    print(json.dumps(after, indent=2))

    print("\n===============================================================")
    print(" COMPARANDO METRICAS ANTES VS DESPUES")
    print("===============================================================")

    diff = DeepDiff(before, after, significant_digits=6)

    if diff:
        print("CAMBIOS DETECTADOS:")
        print(json.dumps(diff, indent=2))
        save_json(diff, f"{base_dir}/nodes_diff.json")
    else:
        print("No hubo cambios detectables en las metricas.")
        save_text("SIN CAMBIOS", f"{base_dir}/nodes_diff.txt")

    print("\n===============================================================")
    print(f" Evidencias generadas en carpeta: {base_dir}")
    print("===============================================================\n")

