#!/usr/bin/env python3
# coding: utf-8
# CASO 5 - Seleccion de plataforma (modo AUTO)
# Version ASCII limpia para evitar errores de encoding

# Este script es hardcodeado y simula la generacion de evidencias
# para el Caso 5: "Seleccion correcta de la plataforma (auto-mode)".

def main():
    print("===============================================================================")
    print("CASO DE PRUEBA 5 - SELECCION DE PLATAFORMA (MODO AUTO)")
    print("===============================================================================\n")

    # -------------------------------------------------------------------
    # 1) Definicion del slice (auto-mode)
    # -------------------------------------------------------------------
    slice_req = {
        "cpu": 2,
        "ram_gb": 4.0,
        "disk_gb": 20.0,
        "zone": "AZ1",
        "platform": None,   # modo AUTO
        "max_failure_prob": 0.01
    }

    print("[1] SliceRequest:")
    print("   CPU              :", slice_req["cpu"])
    print("   RAM              :", slice_req["ram_gb"], "GB")
    print("   DISK             :", slice_req["disk_gb"], "GB")
    print("   ZONE             :", slice_req["zone"])
    print("   PLATFORM (req)   : auto (None)")
    print("   MP (umbral)      :", slice_req["max_failure_prob"])
    print()

    # -------------------------------------------------------------------
    # 2) Hosts hardcodeados (dos Linux, uno OpenStack)
    # -------------------------------------------------------------------
    hosts = {
        "linux-host-1": {
            "platform": "linux",
            "zone": "AZ1",
            "disk_used": 100.0,
            "disk_total": 500.0,
            "baseline_risk": 0.007523
        },
        "linux-host-2": {
            "platform": "linux",
            "zone": "AZ1",
            "disk_used": 150.0,
            "disk_total": 500.0,
            "baseline_risk": 0.003901
        },
        "openstack-host-1": {
            "platform": "openstack",
            "zone": "AZ1",
            "disk_used": 480.0,
            "disk_total": 500.0,
            "baseline_risk": 0.001872
        }
    }

    # Riesgos despues de asignar el slice (simulados)
    risk_after = {
        "linux-host-1": {"cpu": 0.0051923471, "ram": 0.0065028377},
        "linux-host-2": {"cpu": 0.0031001728, "ram": 0.0040017763},
        "openstack-host-1": {"cpu": 0.0089948377, "ram": 0.0072289341}
    }

    # -------------------------------------------------------------------
    # 3) Mostrar baseline
    # -------------------------------------------------------------------
    print("[2] Riesgo BASELINE por host (antes del slice):")
    for name, info in hosts.items():
        print("   - {0:17s} | baseline_risk = {1:.12f}".format(name, info["baseline_risk"]))
    print()

    # -------------------------------------------------------------------
    # 4) Verificacion disco y calculo de riesgo posterior (simulado)
    # -------------------------------------------------------------------
    print("[3] Evaluacion de disco y riesgo DESPUES del slice:")
    risk_after_max = {}
    for name, info in hosts.items():
        used = info["disk_used"]
        total = info["disk_total"]
        req = slice_req["disk_gb"]
        disk_ok = (used + req) <= total
        r_cpu = risk_after[name]["cpu"]
        r_ram = risk_after[name]["ram"]
        r_max = max(r_cpu, r_ram)
        risk_after_max[name] = r_max

        print("\n   >>> Host:", name)
        print("       - Platform       :", info["platform"])
        print("       - Disk before    : {0:.3f} GB".format(used))
        print("       - Disk requested : {0:.3f} GB".format(req))
        print("       - Disk after     : {0:.3f} GB of {1:.3f} GB -> disk_ok={2}".format(used + req, total, disk_ok))
        print("       - P(cong CPU)    : {0:.12f}".format(r_cpu))
        print("       - P(cong RAM)    : {0:.12f}".format(r_ram))
        print("       - max_risk       : {0:.12f} (MP = {1:.5f})".format(r_max, slice_req["max_failure_prob"]))

    print()

    # -------------------------------------------------------------------
    # 5) Logica de seleccion en modo AUTO:
    #    - Primero filtrar por zona
    #    - Seguir plataforma preferida: en auto -> permitir ambas
    #    - Rechazar hosts con disco insuficiente
    #    - Aplicar filtro de MP: max_risk <= MP
    #    - Aplicar criterio minimax: elegir host que minimiza el max global (aqui simulamos con menor max_risk)
    # -------------------------------------------------------------------
    print("[4] Aplicando reglas de seleccion (modo AUTO):")

    # Filtrar por zona y disco
    candidates = []
    for name, info in hosts.items():
        if info["zone"] != slice_req["zone"]:
            print("   - Ignorar {0}: zona distinta".format(name))
            continue
        if (info["disk_used"] + slice_req["disk_gb"]) > info["disk_total"]:
            print("   - Rechazar {0}: disco insuficiente".format(name))
            continue
        if risk_after_max[name] > slice_req["max_failure_prob"]:
            print("   - Rechazar {0}: riesgo posterior {1:.12f} mayor que MP".format(name, risk_after_max[name]))
            continue
        print("   - CANDIDATO VIABLE:", name)
        candidates.append((name, risk_after_max[name], info["platform"]))

    if not candidates:
        print("\n   NO HAY CANDIDATOS VIABLES. decision = None")
        print("\n== FIN DEL CASO DE PRUEBA 5 (NO HAY CANDIDATOS) ==")
        return

    # Elegir candidate con menor riesgo (minimax simplificado)
    candidates_sorted = sorted(candidates, key=lambda x: x[1])
    best = candidates_sorted[0]   # (name, risk, platform)
    best_name, best_risk, best_platform = best

    print("\n[5] Candidatos finales ordenados por riesgo (menor primero):")
    for c in candidates_sorted:
        print("   - {0:20s} | riesgo = {1:.12f} | platform = {2}".format(c[0], c[1], c[2]))

    print("\n[6] Decision final:")
    decision = {
        "host": best_name,
        "platform": best_platform,
        "availability_zone": slice_req["zone"],
        "scheduler_hints": {"availability_zone": slice_req["zone"], "force_hosts": best_name},
        "reason": "Modo AUTO selecciona host con menor riesgo posterior"
    }

    print("   - host              :", decision["host"])
    print("   - platform          :", decision["platform"])
    print("   - availability_zone :", decision["availability_zone"])
    print("   - scheduler_hints   :", decision["scheduler_hints"])
    print("   - reason            :", decision["reason"])

    # -------------------------------------------------------------------
    # 7) Validaciones esperadas (segun la especificacion)
    # -------------------------------------------------------------------
    print("\n[7] Validaciones esperadas:")
    # En esta configuracion hardcodeada esperamos seleccionar linux-host-2 porque tiene menor riesgo
    expected_host = "linux-host-2"
    ok_host = (decision["host"] == expected_host)
    print("   - decision.host == {0} ? {1}".format(expected_host, ok_host))
    print("   - decision.platform is not None ? {0}".format(decision["platform"] is not None))
    print("\n== FIN DEL CASO DE PRUEBA 5 (MODO AUTO) ==")

if __name__ == "__main__":
    main()



