from flask import Flask, jsonify, request
import requests
import time
from flask import send_file
import json
import os


app = Flask(__name__)

# Cambia esto a la IP donde corre Prometheus
PROM_URL = "http://10.20.12.26:9090"   

# Lista de nodos OpenStack + Linux
NODES = {
    "server1": "192.168.201.1:9100",
    "server2": "192.168.201.2:9100",
    "server3": "192.168.201.3:9100",
    "server4": "192.168.201.4:9100",

    "headnode": "192.168.202.1:9100",
    "worker1": "192.168.202.2:9100",
    "worker2": "192.168.202.3:9100",
    "worker3": "192.168.202.4:9100"
}

def prom_query_range(query, hours):
    """Consulta Prometheus para obtener valores históricos."""
    end = int(time.time())
    start = end - hours * 3600
    url = f"{PROM_URL}/api/v1/query_range?query={query}&start={start}&end={end}&step=60"
    return requests.get(url).json()

@app.route("/metrics/<node>")
def get_metrics(node):
    if node not in NODES:
        return jsonify({"error": "node not found"}), 404

    inst = NODES[node]
    hours = int(request.args.get("hours"))

    # CPU %
    q_cpu = f'100 - (avg by (instance)(rate(node_cpu_seconds_total{{instance="{inst}",mode="idle"}}[5m])) * 100)'

    # RAM GB usada
    q_ram = f'(node_memory_MemTotal_bytes{{instance="{inst}"}} - node_memory_MemAvailable_bytes{{instance="{inst}"}})/1024/1024/1024'

    # Disco GB usado
    q_disk = f'(node_filesystem_size_bytes{{instance="{inst}",fstype!="tmpfs"}} - node_filesystem_free_bytes{{instance="{inst}",fstype!="tmpfs"}})/1024/1024/1024'

    cpu = prom_query_range(q_cpu, hours)
    ram = prom_query_range(q_ram, hours)
    disk = prom_query_range(q_disk, hours)

    return jsonify({
        "node": node,
        "cpu": cpu["data"]["result"],
        "ram": ram["data"]["result"],
        "disk": disk["data"]["result"]
    })

##agrego estoooooo
@app.route("/nodes/status", methods=["GET"])
def get_nodes_status():
    """
    Devuelve el JSON completo de nodos con capacidades y uso
    generado por generate_nodes_status.py
    """
    json_path = "nodes_status.json"

    if not os.path.exists(json_path):
        return jsonify({
            "error": "nodes_status.json no existe todavía"
        }), 404

    with open(json_path, "r") as f:
        data = json.load(f)

    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
