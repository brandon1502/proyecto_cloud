#!/usr/bin/env python3
# -- coding: utf-8 --
from vm_placement import (
    SliceRequest,
    HostState,
    decide_vm_placement,
    compute_slice_mu_sigma,
    compute_host_risk_current,
    compute_host_risk_after_assignment,
    check_disk_constraint,
)


def main():
    print("=" * 78)
    print("CASO DE PRUEBA 3 - ELECCION DE ZONA DE DISPONIBILIDAD (AZ)")
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1. Definir SliceRequest (solicitud) para la zona AZ2 y plataforma linux
    # ------------------------------------------------------------------
    slice_req = SliceRequest(
        cpu=1,                    # 1 vCPU
        ram_gb=0.8,               # 0.8 GB de RAM
        disk_gb=1.0,              # 1 GB de disco
        zone="AZ2",               # AZ solicitada
        platform="linux",         # plataforma solicitada
        user_profile="Estudiante",
        technical_context="Cloud / Web / Dev",
        max_failure_prob=0.05     # umbral MP un poco mas relajado
    )

    print("\n[1] SliceRequest:")
    print(f"   CPU              : {slice_req.cpu} vCPUs")
    print(f"   RAM              : {slice_req.ram_gb:.2f} GB")
    print(f"   Disco            : {slice_req.disk_gb:.2f} GB")
    print(f"   Zona             : {slice_req.zone}")
    print(f"   Plataforma       : {slice_req.platform}")
    print(f"   Perfil usuario   : {slice_req.user_profile}")
    print(f"   Contexto tecnico : {slice_req.technical_context}")
    print(f"   Prob. max fallo  : {slice_req.max_failure_prob:.4f}")

    # ------------------------------------------------------------------
    # 2. Definir hosts:
    #    - Uno en AZ1 (debe ser ignorado por zona)
    #    - Dos en AZ2 (uno mas cargado que el otro)
    # ------------------------------------------------------------------

    # Host fuera de la zona solicitada (AZ1) - debe ser ignorado
    host_az1 = HostState(
        name="linux-az1-host",
        platform="linux",
        zone="AZ1",
        cpu_capacity=4,
        ram_gb_capacity=3.8,
        disk_gb_capacity=10.0,
        mu_cpu=1.2,      # carga moderada de CPU
        sigma_cpu=0.4,
        mu_ram_gb=2.0,   # RAM usada
        sigma_ram_gb=0.5,
        disk_gb_used=5.0,
        enabled=True,
        in_maintenance=False,
        metadata={"rack": "RACK-AZ1", "datacenter": "Lima"}
    )

    # Host en AZ2 mas cargado en RAM (riesgo mas alto)
    host_az2_1 = HostState(
        name="linux-az2-host-1",
        platform="linux",
        zone="AZ2",
        cpu_capacity=4,
        ram_gb_capacity=3.8,
        disk_gb_capacity=10.0,
        mu_cpu=1.3,
        sigma_cpu=0.4,
        mu_ram_gb=3.0,   # muy cerca de la capacidad -> mayor riesgo
        sigma_ram_gb=0.35,
        disk_gb_used=6.0,
        enabled=True,
        in_maintenance=False,
        metadata={"rack": "RACK-AZ2-1", "datacenter": "Lima"}
    )

    # Host en AZ2 menos cargado en RAM (deberia ser el elegido)
    host_az2_2 = HostState(
        name="linux-az2-host-2",
        platform="linux",
        zone="AZ2",
        cpu_capacity=4,
        ram_gb_capacity=3.8,
        disk_gb_capacity=10.0,
        mu_cpu=1.0,
        sigma_cpu=0.4,
        mu_ram_gb=2.2,   # mas holgado en RAM
        sigma_ram_gb=0.35,
        disk_gb_used=4.0,
        enabled=True,
        in_maintenance=False,
        metadata={"rack": "RACK-AZ2-2", "datacenter": "Lima"}
    )

    hosts = [host_az1, host_az2_1, host_az2_2]

    # ------------------------------------------------------------------
    # 3. Calcular riesgo BASELINE antes del slice
    # ------------------------------------------------------------------
    baseline_risk = {h.name: compute_host_risk_current(h) for h in hosts}

    print("\n[2] Riesgo BASELINE por host (antes del slice):")
    for h in hosts:
        r = baseline_risk[h.name]
        print(
            f"   - {h.name:18} | zona={h.zone} | plataforma={h.platform} "
            f"| riesgo_base = {r:.10f} ({r:.3e})"
        )

    # Verificacion esperada:
    # Solo para referencia: queremos que en AZ2 haya un host con mas riesgo que el otro
    print("\n[2.1] Comparacion de riesgo baseline en AZ2 (esperamos host-1 > host-2):")
    r_az2_1 = baseline_risk["linux-az2-host-1"]
    r_az2_2 = baseline_risk["linux-az2-host-2"]
    print(f"   - linux-az2-host-1: {r_az2_1:.10f} ({r_az2_1:.3e})")
    print(f"   - linux-az2-host-2: {r_az2_2:.10f} ({r_az2_2:.3e})")
    if r_az2_1 > r_az2_2:
        print("   OK: el host linux-az2-host-1 tiene riesgo baseline mayor que linux-az2-host-2")
    else:
        print("   ADVERTENCIA: el riesgo baseline esperado en AZ2 no cumple host-1 > host-2")

    # ------------------------------------------------------------------
    # 4. Calcular mu/sigma del slice (CPU y RAM) y riesgos DESPUES
    # ------------------------------------------------------------------
    slice_mu_sigma = compute_slice_mu_sigma(slice_req)

    print("\n[3] Parametros mu/sigma del slice (CPU y RAM):")
    mu_cpu, sigma_cpu = slice_mu_sigma["cpu"]
    mu_ram, sigma_ram = slice_mu_sigma["ram"]
    print(f"   CPU: mu={mu_cpu:.6f}, sigma={sigma_cpu:.6f}")
    print(f"   RAM: mu={mu_ram:.6f}, sigma={sigma_ram:.6f}")

    print("\n[4] Verificacion de disco y riesgo DESPUES de asignar el slice:")

    # Evaluar los tres hosts, aunque el algoritmo luego filtrara por zona
    risks_after = {}
    for h in hosts:
        print(f"\n   >>> Host: {h.name}")
        disk_ok = check_disk_constraint(h, slice_req.disk_gb)
        disk_after = h.disk_gb_used + slice_req.disk_gb
        print(f"       - Disco antes     : {h.disk_gb_used:.2f} GB")
        print(f"       - Disco solicitado: {slice_req.disk_gb:.2f} GB")
        print(
            f"       - Disco despues   : {disk_after:.2f} GB de "
            f"{h.disk_gb_capacity:.2f} GB -> disco_ok={disk_ok}"
        )

        ra = compute_host_risk_after_assignment(h, slice_mu_sigma)
        risks_after[h.name] = ra
        p_cpu = ra["cpu"]
        p_ram = ra["ram"]
        max_r = max(ra.values())

        print(
            f"       - P(congestion CPU): {p_cpu:.12f} ({p_cpu:.3e})"
        )
        print(
            f"       - P(congestion RAM): {p_ram:.12f} ({p_ram:.3e})"
        )
        print(
            f"       - max_risk         : {max_r:.12f} ({max_r:.3e}) "
            f"(MP = {slice_req.max_failure_prob:.4f})"
        )

    # ------------------------------------------------------------------
    # 5. Comprobaciones especificas del Caso 3 (zona AZ2)
    # ------------------------------------------------------------------
    print("\n[5] Comprobaciones especificas del Caso 3 (zona AZ2):")

    # 5.1 Verificar que solo se consideren hosts de AZ2 como candidatos logicos
    hosts_az2 = [h for h in hosts if h.zone == slice_req.zone]
    print(f"   - Hosts en la zona solicitada ({slice_req.zone}):")
    for h in hosts_az2:
        print(f"       * {h.name}")

    if all(h.zone == slice_req.zone for h in hosts_az2):
        print("   OK: todos los hosts listados para la zona son efectivamente de AZ2.")
    else:
        print("   ADVERTENCIA: hay hosts en la lista de AZ2 con zona distinta.")

    # 5.2 Verificar que el host mas cargado en AZ2 tenga mayor riesgo despues del slice
    max_risk_az2_1 = max(risks_after["linux-az2-host-1"].values())
    max_risk_az2_2 = max(risks_after["linux-az2-host-2"].values())

    print("\n   - Comparacion de riesgos despues del slice en AZ2:")
    print(f"       max_risk(linux-az2-host-1) = {max_risk_az2_1:.12f} ({max_risk_az2_1:.3e})")
    print(f"       max_risk(linux-az2-host-2) = {max_risk_az2_2:.12f} ({max_risk_az2_2:.3e})")

    if max_risk_az2_1 > max_risk_az2_2:
        print("   OK: el host linux-az2-host-1 tiene riesgo mayor que linux-az2-host-2 en AZ2.")
    else:
        print("   ADVERTENCIA: el host menos cargado no presenta menor riesgo en AZ2.")

    # 5.3 Verificar que ambos pasan la restriccion de disco
    print("\n   - Verificando restriccion de disco en AZ2:")
    for h in hosts_az2:
        ok_disk = check_disk_constraint(h, slice_req.disk_gb)
        print(f"       {h.name}: disco_ok = {ok_disk}")
        if not ok_disk:
            print("       ADVERTENCIA: este host no deberia ser candidato por disco.")

    # ------------------------------------------------------------------
    # 6. Ejecutar decide_vm_placement(...) y validar la decision
    # ------------------------------------------------------------------
    print("\n[6] Ejecutando decide_vm_placement(...)")

    decision = decide_vm_placement(slice_req, hosts)

    if decision is None:
        print("   ERROR: decision es None (no se encontro host viable).")
        return

    print("\n[6.1] Resultado de la decision:")
    print("   PlacementDecision devuelta por el algoritmo:")
    print(f"       - host              : {decision.host}")
    print(f"       - platform          : {decision.platform}")
    print(f"       - availability_zone : {decision.availability_zone}")
    print(f"       - scheduler_hints   : {decision.scheduler_hints}")
    print(f"       - reason            : {decision.reason}")

    # 6.2 Verificar que la decision coincide con lo esperado:
    #     - Se debe elegir un host en AZ2
    #     - Dentro de AZ2, el de menor riesgo: linux-az2-host-2
    print("\n[6.2] Verificando que la decision coincide con lo esperado:")

    esperado_host = "linux-az2-host-2"
    esperado_platform = "linux"
    esperado_zone = "AZ2"

    ok_host = (decision.host == esperado_host)
    ok_platform = (decision.platform == esperado_platform)
    ok_zone = (decision.availability_zone == esperado_zone)

    print(f"   - decision.host == '{esperado_host}' ? {ok_host}")
    print(f"   - decision.platform == '{esperado_platform}' ? {ok_platform}")
    print(f"   - decision.availability_zone == '{esperado_zone}' ? {ok_zone}")

    if ok_host and ok_platform and ok_zone:
        print("   OK: la decision coincide con el host, plataforma y AZ esperados.")
    else:
        print("   ADVERTENCIA: la decision no coincide exactamente con lo esperado.")

    # Comparativa antes / despues para el host seleccionado
    print("\n[6.3] Comparativa antes / despues para el host seleccionado:")
    r_before = baseline_risk[decision.host]
    r_after = max(risks_after[decision.host].values())
    print(f"   Riesgo antes  (baseline) : {r_before:.12f} ({r_before:.3e})")
    print(f"   Riesgo despues (max_risk): {r_after:.12f} ({r_after:.3e})")
    if r_after >= r_before and r_after <= slice_req.max_failure_prob:
        print("   OK: el riesgo del host aumenta pero se mantiene por debajo del umbral MP.")
    else:
        print("   ADVERTENCIA: el comportamiento del riesgo no es el esperado.")

    print("\n== FIN DEL CASO DE PRUEBA 3 (AZ / LINUX) ==")


if __name__ == "__main__":
    main()