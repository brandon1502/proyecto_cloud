import requests
import json
import numpy as np
from datetime import datetime
import sys

NODE_INFO = { "server1": {"zone": "AZ1", "cpu": 4, "ram": 3.8, "disk": 9.6, "platform": "linux"}, "server2": {"zone": "AZ2", "cpu": 4, "ram": 3.8, "disk": 9.6, "platform": "linux"}, "server3": {"zone": "AZ3", "cpu": 4, "ram": 3.8, "disk": 9.6, "platform": "linux"}, "worker1": {"zone": "AZ4", "cpu": 4, "ram": 7.8, "disk": 25.0, "platform": "openstack"}, "worker2": {"zone": "AZ5", "cpu": 4, "ram": 7.8, "disk": 25.0, "platform": "openstack"}, "worker3": {"zone": "AZ5", "cpu": 4, "ram": 7.8, "disk": 25.0, "platform": "openstack"} }

API_URL = "http://localhost:5001/metrics"   # tu API
# Si lo ejecutas en el mismo nodo: http://localhost:5001/metrics

def extract_mean_std(values):
    nums = [float(v[1]) for v in values if v[1] != "NaN"]
    if not nums:
        return {"mean": None, "std": None}
    return {
        "mean": float(np.mean(nums)),
        "std": float(np.std(nums))
    }

def get_node_metrics(node, hours):
    url = f"{API_URL}/{node}?hours={hours}"
    response = requests.get(url, timeout=5).json()   # <-- timeout agregado

    cpu_vals = response["cpu"][0]["values"] if response["cpu"] else []
    ram_vals = response["ram"][0]["values"] if response["ram"] else []
    disk_vals = response["disk"][0]["values"] if response["disk"] else []

    cpu_stats = extract_mean_std(cpu_vals)
    ram_stats = extract_mean_std(ram_vals)

    # DISK: último valor en GiB
    last_disk_gib = float(disk_vals[-1][1]) if disk_vals else None

    # Convertir GiB → GB decimal correctamente
    last_disk_gb = last_disk_gib * 1.073741824 if last_disk_gib is not None else None

    return cpu_stats, ram_stats, last_disk_gb

def main():
    # -------- PARAMETRIZACIÓN DE HOURS --------
    # Si el usuario pasa un valor: python3 script.py 12
    # Si no pasa nada: por defecto 24 horas
    if len(sys.argv) > 1:
        hours = int(sys.argv[1])
    else:
        hours = 24

    print(f"Calculando estado completo de los nodos (últimas {hours} horas)...\n")

    nodes_output = {}

    for node, info in NODE_INFO.items():
        print(f"   ? Procesando {node} (hours={hours})")

        cpu, ram, disk_gb = get_node_metrics(node,hours)

        nodes_output[node] = {
            "id": node,
            "name": f"compute-node-{node}",
            "platform": info["platform"],
            "zone": info["zone"],

            "cpu_capacity": {"value": info["cpu"], "unit": "cores"},
            "ram_capacity": {"value": info["ram"], "unit": "GiB"},
            "disk_capacity": {"value": info["disk"], "unit": "GB"},

            "current_usage": {
                "cpu": {
                    "mean": cpu["mean"],
                    "std": cpu["std"],
                    "unit": "%"
                },
                "ram": {
                    "mean": ram["mean"],
                    "std": ram["std"],
                    "unit": "GiB"
                },
                "disk": {
                    "used": disk_gb,
                    "unit": "GB"
                }
            },

            "enabled": True,
            "in_maintenance": False,

            "metadata": {
                "rack": f"RACK-{info['zone']}",
                "datacenter": "Lima"
            }
        }

    filename = "nodes_status.json"
    with open(filename, "w") as f:
        json.dump(nodes_output, f, indent=4)

    print(f"\n? Archivo generado con exito: {filename}")

if __name__ == "__main__":
    main()
