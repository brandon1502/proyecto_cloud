#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vm_placement import (
    SliceRequest,
    HostState,
    PlacementDecision,
    decide_vm_placement,
    compute_slice_mu_sigma,
    compute_host_risk_current,
    compute_host_risk_after_assignment,
    check_disk_constraint,
)


def main():
    print("=" * 78)
    print("CASO DE PRUEBA 2 - SELECCION POR RAM EN LINUX / AZ1")
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1) Solicitud del slice (input simulado)
    # ------------------------------------------------------------------
    slice_req = SliceRequest(
        cpu=1,                     # 1 vCPU
        ram_gb=0.8,                # 0.8 GB adicionales
        disk_gb=1.0,               # 1 GB de disco
        zone="AZ1",
        platform="linux",
        user_profile="Estudiante",
        technical_context="Cloud / Web / Dev",
        max_failure_prob=0.01,     # MP = 1 %
    )

    print("\n[1] SliceRequest:")
    print(f"   CPU              : {slice_req.cpu} vCPUs")
    print(f"   RAM              : {slice_req.ram_gb} GB")
    print(f"   Disco            : {slice_req.disk_gb} GB")
    print(f"   Zona             : {slice_req.zone}")
    print(f"   Plataforma       : {slice_req.platform}")
    print(f"   Perfil usuario   : {slice_req.user_profile}")
    print(f"   Contexto tecnico : {slice_req.technical_context}")
    print(f"   Prob. max fallo  : {slice_req.max_failure_prob}")

    # ------------------------------------------------------------------
    # 2) Estado de los hosts Linux en AZ1 (valores inspirados en Grafana)
    # ------------------------------------------------------------------
    linux_host_1 = HostState(
        name="linux-host-1",
        platform="linux",
        zone="AZ1",
        cpu_capacity=4,
        ram_gb_capacity=4.0,
        disk_gb_capacity=10.0,

        mu_cpu=0.30,
        sigma_cpu=0.10,

        # RAM ~ 90 % de 4 GB = 3.6 GB (host mas cargado)
        mu_ram_gb=3.6,
        sigma_ram_gb=0.15,

        disk_gb_used=7.2,   # ~72 % de 10 GB

        enabled=True,
        in_maintenance=False,
        metadata={"fuente": "valores aproximados desde Grafana"},
    )

    linux_host_2 = HostState(
        name="linux-host-2",
        platform="linux",
        zone="AZ1",
        cpu_capacity=4,
        ram_gb_capacity=4.0,
        disk_gb_capacity=10.0,

        mu_cpu=0.20,
        sigma_cpu=0.10,

        # RAM ~ 83 % de 4 GB = 3.3 GB (host menos cargado)
        mu_ram_gb=3.3,
        sigma_ram_gb=0.15,

        disk_gb_used=6.35,  # ~63.5 % de 10 GB

        enabled=True,
        in_maintenance=False,
        metadata={"fuente": "valores aproximados desde Grafana"},
    )

    hosts = [linux_host_1, linux_host_2]

    # ------------------------------------------------------------------
    # 3) Riesgo actual (baseline) antes de asignar el slice
    # ------------------------------------------------------------------
    print("\n[2] Riesgo BASELINE por host (antes del slice):")
    baseline_risk = {}
    for h in hosts:
        r = compute_host_risk_current(h)
        baseline_risk[h.name] = r
        print(
            "   - {name:13s} | zona={zone} | plataforma={plat} "
            "| riesgo_base = {risk:.10g}".format(
                name=h.name,
                zone=h.zone,
                plat=h.platform,
                risk=r,
            )
        )

    # Evidencia: host1 tiene mayor riesgo baseline que host2
    assert baseline_risk["linux-host-1"] > baseline_risk["linux-host-2"], \
        "Se esperaba que linux-host-1 tenga mayor riesgo baseline que linux-host-2"

    # ------------------------------------------------------------------
    # 4) mu/sigma del slice y riesgos despues de asignarlo
    # ------------------------------------------------------------------
    slice_mu_sigma = compute_slice_mu_sigma(slice_req)

    print("\n[3] Parametros mu/sigma del slice (solo CPU y RAM):")
    print(
        "   CPU: mu={:.10g}, sigma={:.10g}".format(
            slice_mu_sigma["cpu"][0],
            slice_mu_sigma["cpu"][1],
        )
    )
    print(
        "   RAM: mu={:.10g}, sigma={:.10g}".format(
            slice_mu_sigma["ram"][0],
            slice_mu_sigma["ram"][1],
        )
    )

    print("\n[4] Verificacion de disco y riesgo DESPUES de asignar el slice:")

    riesgos_despues = {}
    for h in hosts:
        print("\n   >>> Host: {}".format(h.name))
        disk_ok = check_disk_constraint(h, slice_req.disk_gb)
        disk_total = h.disk_gb_used + slice_req.disk_gb
        print("       - Disco antes     : {:.4f} GB".format(h.disk_gb_used))
        print("       - Disco solicitado: {:.4f} GB".format(slice_req.disk_gb))
        print(
            "       - Disco despues   : {:.4f} GB de {:.4f} GB -> disco_ok={}".format(
                disk_total,
                h.disk_gb_capacity,
                disk_ok,
            )
        )

        r_after = compute_host_risk_after_assignment(h, slice_mu_sigma)
        riesgos_despues[h.name] = r_after
        print("       - P(congestion CPU): {:.10g}".format(r_after["cpu"]))
        print("       - P(congestion RAM): {:.10g}".format(r_after["ram"]))
        print(
            "       - max_risk         : {:.10g} (MP = {:.5f})".format(
                max(r_after.values()),
                slice_req.max_failure_prob,
            )
        )

    # ------------------------------------------------------------------
    # 5) Comprobaciones de las evidencias del caso
    # ------------------------------------------------------------------
    print("\n[5] Comprobaciones de las condiciones del Caso 2:")

    max_risk_host1 = max(riesgos_despues["linux-host-1"].values())
    max_risk_host2 = max(riesgos_despues["linux-host-2"].values())

    # 5.1 linux-host-1 (mas cargado)
    print("   - Verificando condiciones para linux-host-1:")
    assert max_risk_host1 > slice_req.max_failure_prob, \
        "Se esperaba que el riesgo de linux-host-1 supere MP"
    assert max_risk_host1 > max_risk_host2, \
        "Se esperaba que linux-host-1 tenga mas riesgo que linux-host-2"
    print("     OK: max_risk_host1 es mayor que MP y mayor que max_risk_host2.")

    # 5.2 linux-host-2
    print("   - Verificando condiciones para linux-host-2:")
    assert check_disk_constraint(linux_host_2, slice_req.disk_gb), \
        "Se esperaba disco suficiente en linux-host-2"
    assert max_risk_host2 <= slice_req.max_failure_prob, \
        "Se esperaba que max_risk_host2 sea menor o igual a MP"
    print("     OK: disco suficiente y riesgo dentro del umbral MP.")

    # 5.3 Comparativa antes/despues de linux-host-2
    print("   - Comparando riesgo antes y despues en linux-host-2:")
    R_before = baseline_risk["linux-host-2"]
    R_after = max_risk_host2
    print("     R_before = {:.10g}".format(R_before))
    print("     R_after  = {:.10g}".format(R_after))
    assert R_after > R_before, \
        "Se esperaba que el riesgo despues sea ligeramente mayor (mas carga)"
    assert R_after <= slice_req.max_failure_prob, \
        "R_after debe seguir menor o igual que MP"
    print("     OK: R_after > R_before y R_after <= MP.")

    # ------------------------------------------------------------------
    # 6) Ejecutar decide_vm_placement(...)
    # ------------------------------------------------------------------
    print("\n[6] Ejecutando decide_vm_placement(...)\n")
    decision = decide_vm_placement(slice_req, hosts)

    print("[6.1] Resultado de la decision:")
    assert decision is not None, "Se esperaba una decision valida (no None)"
    print("   PlacementDecision devuelta por el algoritmo:")
    print("       - host              : {}".format(decision.host))
    print("       - platform          : {}".format(decision.platform))
    print("       - availability_zone : {}".format(decision.availability_zone))
    print("       - scheduler_hints   : {}".format(decision.scheduler_hints))
    print("       - reason            : {}".format(decision.reason))

    # 6.2 Verificar que la decision sea la esperada
    print("\n[6.2] Verificando que la decision coincide con lo esperado:")
    assert decision.host == "linux-host-2", \
        "Se esperaba que el host seleccionado sea linux-host-2"
    assert decision.platform == "linux", \
        "Se esperaba que la plataforma seleccionada sea linux"
    assert decision.availability_zone == "AZ1", \
        "Se esperaba que la AZ seleccionada sea AZ1"
    print("   OK: la decision coincide con el host y la plataforma esperados.")

    print("\n== FIN DEL CASO DE PRUEBA 2 (RAM / LINUX / AZ1) ==")


if __name__ == "__main__":
    main()
