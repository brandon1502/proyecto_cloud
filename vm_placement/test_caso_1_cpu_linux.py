#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Caso de prueba 1:
Seleccion del host Linux por CPU en la zona AZ1.

Escenario:
- Dos hosts Linux en AZ1 que representan a "server1" y "server2".
- Ambos tienen 4 vCPU, 4 GB de RAM y 10 GB de disco.
- server1 esta mas cargado (CPU y RAM cerca al 90 %, disco ~72 %).
- server2 esta menos cargado (CPU y RAM algo menores, disco ~63 %).

Objetivo:
- Verificar que el modulo de placement NO elige al host mas cargado
  (riesgo de congestion mayor al umbral) y selecciona el host mas
  liviano en CPU respetando max_failure_prob.
"""

from typing import Dict, List
from vm_placement import (
    SliceRequest,
    HostState,
    PlacementDecision,
    compute_slice_mu_sigma,
    compute_host_risk_after_assignment,
    compute_host_risk_current,
    check_disk_constraint,
    decide_vm_placement,
)


def formatear_prob(p: float) -> str:
    """
    Formatea una probabilidad para que no se vea siempre como 0.000000.
    - Si p >= 1e-4 se muestra con 6 decimales.
    - Si p < 1e-4 se muestra en notacion cientifica con 3 decimales.
    """
    if p == 0.0:
        return "0"
    if p >= 1e-4:
        return f"{p:.6f}"
    return f"{p:.3e}"


def construir_hosts() -> List[HostState]:
    """
    Construye dos hosts Linux que se parecen a tus server1 y server2
    segun los dashboards de Grafana.

    Ambos con:
      - 4 vCPU
      - 4 GB RAM
      - 10 GB disco

    server1: mas cargado
      - CPU media ~3 cores (75 % de 4)
      - RAM media ~3.6 GB  (90 % de 4)
      - Disco usado ~7.2 GB (72 % de 10)

    server2: menos cargado
      - CPU media ~2 cores  (50 % de 4)
      - RAM media ~3.3 GB   (82.5 % de 4)
      - Disco usado ~6.3 GB (63 % de 10)
    """

    linux_server1 = HostState(
        name="linux-server1",
        platform="linux",
        zone="AZ1",
        cpu_capacity=4,
        ram_gb_capacity=4.0,
        disk_gb_capacity=10.0,
        # consumo a largo plazo (medias y desv. estandar)
        mu_cpu=3.0,
        sigma_cpu=0.4,
        mu_ram_gb=3.6,
        sigma_ram_gb=0.2,
        disk_gb_used=7.2,
        enabled=True,
        in_maintenance=False,
        metadata={"entorno": "linux", "origen": "grafana-server1-aprox"},
    )

    linux_server2 = HostState(
        name="linux-server2",
        platform="linux",
        zone="AZ1",
        cpu_capacity=4,
        ram_gb_capacity=4.0,
        disk_gb_capacity=10.0,
        mu_cpu=2.0,
        sigma_cpu=0.4,
        mu_ram_gb=3.3,
        sigma_ram_gb=0.25,
        disk_gb_used=6.3,
        enabled=True,
        in_maintenance=False,
        metadata={"entorno": "linux", "origen": "grafana-server2-aprox"},
    )

    return [linux_server1, linux_server2]


def construir_slice() -> SliceRequest:
    """
    Slice de prueba para este caso:

    - 1 vCPU
    - 1 GB de RAM
    - 1 GB de disco
    - Zona AZ1
    - Plataforma linux
    - Perfil Estudiante
    - Contexto Cloud / Web / Dev
    - max_failure_prob = 1 % (0.01)
    """
    return SliceRequest(
        cpu=1,
        ram_gb=1.0,
        disk_gb=1.0,
        zone="AZ1",
        platform="linux",
        user_profile="Estudiante",
        technical_context="Cloud / Web / Dev",
        max_failure_prob=0.01,
    )


def main():
    print("=" * 80)
    print("CASO DE PRUEBA 1 - SELECCION POR CPU EN LINUX / AZ1")
    print("=" * 80)

    # 1) Construir slice de prueba
    slice_req = construir_slice()

    print("\n[1] SliceRequest (entrada simulada):")
    print(f"   CPU              : {slice_req.cpu} vCPU")
    print(f"   RAM              : {slice_req.ram_gb} GB")
    print(f"   Disco            : {slice_req.disk_gb} GB")
    print(f"   Zona             : {slice_req.zone}")
    print(f"   Plataforma       : {slice_req.platform}")
    print(f"   Perfil usuario   : {slice_req.user_profile}")
    print(f"   Contexto tecnico : {slice_req.technical_context}")
    print(f"   Max failure prob : {slice_req.max_failure_prob}")

    # 2) Construir hosts (representan server1 y server2)
    hosts = construir_hosts()

    # 3) Riesgo base de cada host antes de asignar el slice
    print("\n[2] Riesgo base por host (antes del slice):")
    baseline = {}
    for h in hosts:
        r = compute_host_risk_current(h)
        baseline[h.name] = r
        print(
            f"   - {h.name:13} | zona={h.zone} | plataforma={h.platform} "
            f"| riesgo_base = {formatear_prob(r)}"
        )

    # 4) Calcular contribucion del slice en mu y sigma (CPU y RAM)
    slice_mu_sigma = compute_slice_mu_sigma(slice_req)

    print("\n[3] Verificacion de disco y riesgo DESPUES de asignar el slice:")
    for h in hosts:
        print(f"\n   >>> Host: {h.name}")
        # disco
        ok_disco = check_disk_constraint(h, slice_req.disk_gb)
        disco_despues = h.disk_gb_used + slice_req.disk_gb
        print(
            f"       - Disco antes: {h.disk_gb_used:.2f} GB, "
            f"despues: {disco_despues:.2f} GB de {h.disk_gb_capacity:.2f} GB "
            f"-> disco_ok={ok_disco}"
        )

        # riesgo despues
        riesgos = compute_host_risk_after_assignment(h, slice_mu_sigma)
        p_cpu = riesgos["cpu"]
        p_ram = riesgos["ram"]
        max_riesgo = max(p_cpu, p_ram)

        print(f"       - P(congestion CPU): {formatear_prob(p_cpu)}")
        print(f"       - P(congestion RAM): {formatear_prob(p_ram)}")
        print(
            f"       - Riesgo maximo     : {formatear_prob(max_riesgo)} "
            f"(MP = {slice_req.max_failure_prob})"
        )

    # 5) Ejecutar el algoritmo real de placement
    print("\n[4] Ejecutando decide_vm_placement(...)")
    decision: PlacementDecision | None = decide_vm_placement(slice_req, hosts)

    # 6) Mostrar comparativa antes / despues para el host elegido
    print("\n[5] Resultado del caso de prueba:")

    if decision is None:
        print("   ERROR: El algoritmo no encontro un host viable.")
        print("   Este caso deberia devolver un host Linux en AZ1.")
        return

    # buscar el host seleccionado en la lista
    host_sel = next(h for h in hosts if h.name == decision.host)

    # recalcular riesgos despues para el host seleccionado
    riesgos_sel = compute_host_risk_after_assignment(host_sel, slice_mu_sigma)
    riesgo_before = baseline[host_sel.name]
    riesgo_after = max(riesgos_sel.values())

    print("   Decision devuelta por el algoritmo:")
    print(f"       - host              : {decision.host}")
    print(f"       - plataforma        : {decision.platform}")
    print(f"       - availability_zone : {decision.availability_zone}")
    print(f"       - scheduler_hints   : {decision.scheduler_hints}")
    print(f"       - razon             : {decision.reason}")

    print("\n   Comparativa de riesgo para el host seleccionado:")
    print(f"       - Riesgo antes  : {formatear_prob(riesgo_before)}")
    print(f"       - Riesgo despues: {formatear_prob(riesgo_after)}")

    print("\n== FIN DEL CASO DE PRUEBA 1 ==\n")


if __name__ == "__main__":
    main()
