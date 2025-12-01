#!/usr/bin/env python3

"""
CASO 4 - FALLBACK POR DISCO INSUFICIENTE
Prueba: Ningun host debe ser viable porque ambos tienen disco insuficiente.
"""

from vm_placement import SliceRequest, HostState, decide_vm_placement, compute_host_risk_current
from math import sqrt

# ------------------------------------------------------------------------------
# Hosts para el Caso 4 (disco insuficiente)
# ------------------------------------------------------------------------------

host1 = HostState(
    name="linux-host-1",
    platform="linux",
    zone="AZ1",
    cpu_capacity=64,
    ram_gb_capacity=256,
    disk_gb_capacity=10.0,        # MUY BAJO: el slice pide 20 GB
    mu_cpu=10.0,
    sigma_cpu=2.0,
    mu_ram_gb=40.0,
    sigma_ram_gb=5.0,
    disk_gb_used=9.0,             # Ya casi lleno
    enabled=True,
    in_maintenance=False,
    metadata={}
)

host2 = HostState(
    name="linux-host-2",
    platform="linux",
    zone="AZ1",
    cpu_capacity=64,
    ram_gb_capacity=256,
    disk_gb_capacity=15.0,        # Tambien insuficiente
    mu_cpu=8.0,
    sigma_cpu=1.5,
    mu_ram_gb=30.0,
    sigma_ram_gb=4.0,
    disk_gb_used=14.0,            # Ya casi lleno
    enabled=True,
    in_maintenance=False,
    metadata={}
)

hosts = [host1, host2]

# ------------------------------------------------------------------------------
# Slice que no cabe en ningun host
# ------------------------------------------------------------------------------

slice_req = SliceRequest(
    cpu=2,
    ram_gb=4.0,
    disk_gb=20.0,     # ESTE DISCO ES MAYOR QUE LA CAPACIDAD DISPONIBLE DE AMBOS
    zone="AZ1",
    platform="linux",
    user_profile="Estudiante",
    technical_context="Cloud / Web / Dev",
    max_failure_prob=0.01
)

print("\n==============================================================================")
print("CASO DE PRUEBA 4 - FALLBACK POR DISCO INSUFICIENTE")
print("==============================================================================\n")

print("[1] SliceRequest:")
print(f"   CPU: {slice_req.cpu}")
print(f"   RAM: {slice_req.ram_gb}")
print(f"   Disk: {slice_req.disk_gb}")
print(f"   Zone: {slice_req.zone}")
print(f"   Platform: {slice_req.platform}")
print(f"   MP: {slice_req.max_failure_prob}")

# ------------------------------------------------------------------------------
# Riesgo Baseline
# ------------------------------------------------------------------------------

print("\n[2] Baseline risk antes del slice:")
baseline = {}
for h in hosts:
    risk = compute_host_risk_current(h)
    baseline[h.name] = risk
    print(f"   - {h.name}: baseline = {risk:.12f}")

# ------------------------------------------------------------------------------
# Verificacion de disco
# ------------------------------------------------------------------------------

def check_disk(host, req):
    return host.disk_gb_used + req.disk_gb <= host.disk_gb_capacity

print("\n[3] Verificando disco antes de ejecutar placement:")

for h in hosts:
    used = h.disk_gb_used
    req = slice_req.disk_gb
    cap = h.disk_gb_capacity
    ok = check_disk(h, slice_req)
    print(f"   Host: {h.name}")
    print(f"      Disco usado: {used}  + solicitado: {req}  = total {used+req} de {cap}")
    print(f"      Suficiente? {ok}")

# ------------------------------------------------------------------------------
# Ejecutar algoritmo principal
# ------------------------------------------------------------------------------

print("\n[4] Ejecutando decide_vm_placement...")
decision = decide_vm_placement(slice_req, hosts)

print("\n[5] Resultado de la decision:")
if decision is None:
    print("   OK: decision es None (esperado). No hay hosts viables por disco insuficiente.")
else:
    print("   ERROR: se obtuvo una decision cuando NO deberia haber ninguna!")
    print(decision)

print("\n== FIN DEL CASO DE PRUEBA 4 ==")