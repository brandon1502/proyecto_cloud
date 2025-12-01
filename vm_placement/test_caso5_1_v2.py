#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import math

PLACEMENT_URL = "http://localhost:5004/api/v1/placement"
NODES_URL = "http://localhost:5001/nodes/status"


# ========= HELPERS TEORICOS (misma logica que vm_placement.py) =========

PROFILE_TABLE = {
    "Estudiante":    {"mu_cpu": 0.10, "sigma_cpu": 0.05, "mu_ram": 0.15, "sigma_ram": 0.05},
    "JP / Junior":   {"mu_cpu": 0.20, "sigma_cpu": 0.10, "mu_ram": 0.25, "sigma_ram": 0.10},
    "Profesor":      {"mu_cpu": 0.35, "sigma_cpu": 0.15, "mu_ram": 0.40, "sigma_ram": 0.15},
    "Tesista":       {"mu_cpu": 0.45, "sigma_cpu": 0.20, "mu_ram": 0.50, "sigma_ram": 0.20},
    "Investigador":  {"mu_cpu": 0.60, "sigma_cpu": 0.25, "mu_ram": 0.70, "sigma_ram": 0.25},
}

CONTEXT_TABLE = {
    "Cloud / Web / Dev":       {"f_cpu": 0.8, "f_ram": 0.7, "v": 1.0},
    "SDN / Redes":             {"f_cpu": 0.7, "f_ram": 0.5, "v": 1.0},
    "Big Data":                {"f_cpu": 1.2, "f_ram": 1.4, "v": 1.3},
    "IA / Machine Learning":   {"f_cpu": 1.5, "f_ram": 1.3, "v": 1.3},
    "HPC / Computo intensivo": {"f_cpu": 2.0, "f_ram": 1.5, "v": 1.5},
    "Virtualizacion general":  {"f_cpu": 1.0, "f_ram": 1.0, "v": 1.1},
}


def _fmt_prob(p: float) -> str:
    # Formato amigable para probabilidades
    if p == 0.0:
        return "~0"
    elif p < 1e-6:
        return f"{p:.2e}"
    else:
        return f"{p:.6f}"


def _normal_tail_probability(ci: float, mu: float, sigma: float) -> float:
    # P_cong = P(DT > CI) para DT ~ N(mu, sigma^2)
    if sigma <= 0:
        return 0.0 if ci >= mu else 1.0

    x = (ci - mu) / sigma
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def _compute_slice_mu_sigma(cpu: int,
                            ram_gb: float,
                            user_profile: str,
                            technical_context: str):
    # Replica compute_slice_mu_sigma de vm_placement.py
    p = PROFILE_TABLE.get(user_profile, PROFILE_TABLE["Estudiante"])
    c = CONTEXT_TABLE.get(technical_context, CONTEXT_TABLE["Virtualizacion general"])

    mu_cpu_pct = p["mu_cpu"] * c["f_cpu"]
    sigma_cpu_pct = p["sigma_cpu"] * c["f_cpu"] * c["v"]

    mu_ram_pct = p["mu_ram"] * c["f_ram"]
    sigma_ram_pct = p["sigma_ram"] * c["f_ram"] * c["v"]

    mu_cpu = mu_cpu_pct * cpu
    sigma_cpu = sigma_cpu_pct * cpu

    mu_ram = mu_ram_pct * ram_gb
    sigma_ram = sigma_ram_pct * ram_gb

    return (mu_cpu, sigma_cpu), (mu_ram, sigma_ram)


# ========================= SCRIPT DE TEST =========================

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


def analisis_teorico_sin_zona(payload: dict, nodes_data: dict):
    print("\n" + "=" * 70)
    print("2) ANALISIS TEORICO SIN RESTRICCION DE ZONA")
    print("=" * 70)

    cpu_req = int(payload["cpu"])
    ram_req = float(payload["ram_gb"])
    user_profile = payload.get("user_profile", "Estudiante")
    technical_context = payload.get("technical_context", "Virtualizacion general")

    print("\nUsando mismo slice pedido a la API:")
    print(f"  CPU reservada: {cpu_req} cores")
    print(f"  RAM reservada: {ram_req} GB")
    print(f"  Perfil: {user_profile}")
    print(f"  Contexto: {technical_context}\n")

    (mu_cpu_slice, sigma_cpu_slice), (mu_ram_slice, sigma_ram_slice) = \
        _compute_slice_mu_sigma(cpu_req, ram_req, user_profile, technical_context)

    print("Riesgo teorico por host (ignorando zona):")
    print("-" * 70)
    print(f"{'Host':25} {'Zone':5} {'Plat':8} {'Pcpu':>12} {'Pram':>12} {'Pmax':>12}")
    print("-" * 70)

    best_host = None
    best_pmax = None
    best_zone = None
    best_plat = None

    for node_id, node in nodes_data.items():
        cpu_capacity = float(node["cpu_capacity"]["value"])
        ram_capacity = float(node["ram_capacity"]["value"])

        cpu_stats = node["current_usage"]["cpu"]
        ram_stats = node["current_usage"]["ram"]

        # Igual que parse_worker_to_hoststate: porcentaje -> cores
        mu_cpu_host = float(cpu_stats["mean"]) * cpu_capacity / 100.0
        sigma_cpu_host = float(cpu_stats["std"]) * cpu_capacity / 100.0

        mu_ram_host = float(ram_stats["mean"])
        sigma_ram_host = float(ram_stats["std"])

        # Suma de normales: DT = host + slice
        mu_dt_cpu = mu_cpu_host + mu_cpu_slice
        sigma_dt_cpu = math.sqrt(sigma_cpu_host ** 2 + sigma_cpu_slice ** 2)

        mu_dt_ram = mu_ram_host + mu_ram_slice
        sigma_dt_ram = math.sqrt(sigma_ram_host ** 2 + sigma_ram_slice ** 2)

        p_cpu = _normal_tail_probability(cpu_capacity, mu_dt_cpu, sigma_dt_cpu)
        p_ram = _normal_tail_probability(ram_capacity, mu_dt_ram, sigma_dt_ram)
        p_max = max(p_cpu, p_ram)

        print(f"{node['name']:25} {node['zone']:5} {node['platform']:8} "
              f"{_fmt_prob(p_cpu):>12} {_fmt_prob(p_ram):>12} {_fmt_prob(p_max):>12}")

        if best_pmax is None or p_max < best_pmax:
            best_pmax = p_max
            best_host = node["name"]
            best_zone = node["zone"]
            best_plat = node["platform"]

    print("-" * 70)
    print("\nHost con MENOR riesgo teorico (ignorando zona y plataforma):")
    print(f"  -> {best_host} en zona {best_zone} (platform={best_plat}), "
          f"Pmax ~ {_fmt_prob(best_pmax)}\n")


def probar_placement_por_zona(payload: dict):
    zone = payload["zone"]

    print("\n" + "=" * 70)
    print(f"3) SOLICITUD REAL DE PLACEMENT PARA LA ZONA {zone}")
    print("=" * 70)

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

    print("\nConclusion:")
    print(f"  - La API respeto la zona de disponibilidad solicitada ({zone}).")


if __name__ == "__main__":
    # 1) Mostrar hosts
    nodes_data = mostrar_hosts_y_zonas()

    # Mismo slice de prueba
    payload = {
        "cpu": 1,
        "ram_gb": 1.0,
        "disk_gb": 1.0,
        "zone": "AZ4",                # cambia aqui si quieres otra AZ
        "platform": "openstack",
        "user_profile": "Estudiante",
        "technical_context": "Virtualizacion general"
    }

    # 2) Primero: analisis teorico SIN restriccion de zona
    analisis_teorico_sin_zona(payload, nodes_data)

    # 3) Segundo: llamada real a la API con restriccion de AZ
    probar_placement_por_zona(payload)
