#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de VM Placement para el orquestador PUCP.

Implementa:
- Interpretación de requerimientos de usuario
- Filtro de viabilidad basado en probabilidad de congestión (DTMP implícita)
- Selección Minimax de servidor
- Soporte unificado para Linux y OpenStack

IMPORTANTE: Disco es tratado como restricción DETERMINISTA (no probabilística)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Tuple
import math

# ==========================
#   TIPOS BÁSICOS
# ==========================

Platform = Literal["linux", "openstack"]

@dataclass
class SliceRequest:
    """
    Requerimiento de slice que llega al módulo de Placement.
    Esta estructura cumple con lo que pide el laboratorio:
    CPU, RAM, Disco, zona y plataforma preferida.
    """
    cpu: int                  # vCPUs totales del slice (suma de todas las VMs)
    ram_gb: float             # RAM total del slice en GB
    disk_gb: float            # Disco total del slice en GB (DETERMINISTA)

    zone: str                 # AZ requerida
    platform: Optional[Platform] = None     # "linux", "openstack" o None/"auto"
    user_profile: str = "Estudiante"        # perfil (Tabla 1 del PDF)
    technical_context: str = "Virtualización general"  # contexto (Tabla 2)
    max_failure_prob: float = 0.01          # MP: prob. máxima de fallo permitida


@dataclass
class HostState:
    """
    Estado de cada host físico del clúster (Linux u OpenStack).
    Incluye:
    - Capacidad instalada (CI_k)
    - Consumo a largo plazo existente (μ_LP, σ_LP) por recurso
    - Metadatos (zona, plataforma, mantenimiento, etc.)
    """
    name: str
    platform: Platform
    zone: str

    cpu_capacity: int       # CI_cpu en cores
    ram_gb_capacity: float  # CI_ram en GB
    disk_gb_capacity: float # CI_disk en GB

    # Consumo a largo plazo actual (CCLP) - SOLO CPU Y RAM son probabilísticos
    mu_cpu: float
    sigma_cpu: float
    mu_ram_gb: float
    sigma_ram_gb: float
    
    # Disco usado actual (DETERMINISTA - no tiene sigma)
    disk_gb_used: float     # Disco ya usado en el host (determinista)

    enabled: bool = True
    in_maintenance: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class PlacementDecision:
    """
    Decisión final de colocación que el módulo devuelve al orquestador.
    Coincide con lo que piden en el enunciado (host + plataforma + args extra).
    """
    host: str
    platform: Platform
    availability_zone: str
    scheduler_hints: Dict[str, str] = field(default_factory=dict)
    reason: str = ""   # explicación corta (opcional)


# ==========================
#   PARÁMETROS DEL MODELO
#   (Tablas del PDF)
# ==========================

# Tabla 1: consumo base por perfil (en % expresado como fracción)
# SOLO CPU Y RAM (disco removido porque es determinista)
PROFILE_TABLE = {
    "Estudiante":    {"mu_cpu": 0.10, "sigma_cpu": 0.05, "mu_ram": 0.15, "sigma_ram": 0.05},
    "JP / Junior":   {"mu_cpu": 0.20, "sigma_cpu": 0.10, "mu_ram": 0.25, "sigma_ram": 0.10},
    "Profesor":      {"mu_cpu": 0.35, "sigma_cpu": 0.15, "mu_ram": 0.40, "sigma_ram": 0.15},
    "Tesista":       {"mu_cpu": 0.45, "sigma_cpu": 0.20, "mu_ram": 0.50, "sigma_ram": 0.20},
    "Investigador":  {"mu_cpu": 0.60, "sigma_cpu": 0.25, "mu_ram": 0.70, "sigma_ram": 0.25},
}

# Tabla 2: factores de intensidad y variabilidad por contexto técnico
# SOLO CPU Y RAM (disco removido porque es determinista)
CONTEXT_TABLE = {
    "Cloud / Web / Dev":        {"f_cpu": 0.8, "f_ram": 0.7, "v": 1.0},
    "SDN / Redes":              {"f_cpu": 0.7, "f_ram": 0.5, "v": 1.0},
    "Big Data":                 {"f_cpu": 1.2, "f_ram": 1.4, "v": 1.3},
    "IA / Machine Learning":    {"f_cpu": 1.5, "f_ram": 1.3, "v": 1.3},
    "HPC / Cómputo intensivo":  {"f_cpu": 2.0, "f_ram": 1.5, "v": 1.5},
    "Virtualización general":   {"f_cpu": 1.0, "f_ram": 1.0, "v": 1.1},
}

# ==========================
#   FUNCIONES AUXILIARES
# ==========================

def _normal_tail_probability(ci: float, mu: float, sigma: float) -> float:
    """
    P_cong = P(DT > CI) para DT ~ N(mu, sigma^2).
    Usamos la relación con la cola de la Normal estándar: Q(x) = 0.5 * erfc(x / sqrt(2)).
    Si sigma = 0, interpretamos que no hay variabilidad.
    """
    if sigma <= 0:
        return 0.0 if ci >= mu else 1.0

    x = (ci - mu) / sigma  # variable estandarizada
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def _get_profile_entry(profile: str) -> Dict[str, float]:
    return PROFILE_TABLE.get(profile, PROFILE_TABLE["Estudiante"])


def _get_context_entry(context: str) -> Dict[str, float]:
    return CONTEXT_TABLE.get(context, CONTEXT_TABLE["Virtualización general"])


def compute_slice_mu_sigma(slice_req: SliceRequest) -> Dict[str, Tuple[float, float]]:
    """
    A partir de:
    - Perfil de usuario
    - Contexto técnico
    - Recursos reservados (cpu, ram_gb)

    Calcula μ_slice,k y σ_slice,k en unidades físicas (cores, GB)
    SOLO para CPU y RAM (disco es determinista)
    """
    p = _get_profile_entry(slice_req.user_profile)
    c = _get_context_entry(slice_req.technical_context)

    # Porcentajes ajustados (en fracción)
    mu_cpu_pct = p["mu_cpu"] * c["f_cpu"]
    sigma_cpu_pct = p["sigma_cpu"] * c["f_cpu"] * c["v"]

    mu_ram_pct = p["mu_ram"] * c["f_ram"]
    sigma_ram_pct = p["sigma_ram"] * c["f_ram"] * c["v"]

    # Pasar de porcentaje a unidades físicas (multiplicar por recursos reservados R)
    mu_cpu = mu_cpu_pct * slice_req.cpu
    sigma_cpu = sigma_cpu_pct * slice_req.cpu

    mu_ram = mu_ram_pct * slice_req.ram_gb
    sigma_ram = sigma_ram_pct * slice_req.ram_gb

    return {
        "cpu": (mu_cpu, sigma_cpu),
        "ram": (mu_ram, sigma_ram),
    }


def check_disk_constraint(host: HostState, disk_requested_gb: float) -> bool:
    """
    Verifica restricción DETERMINISTA de disco:
    disco_usado + disco_solicitado <= capacidad_disco
    
    Parámetros:
    -----------
    host : HostState
        Host a evaluar
    disk_requested_gb : float
        Disco solicitado por el slice (GB)
    
    Retorna:
    --------
    bool : True si cumple la restricción, False en caso contrario
    """
    disk_after = host.disk_gb_used + disk_requested_gb
    return disk_after <= host.disk_gb_capacity


def compute_host_risk_after_assignment(
    host: HostState,
    slice_mu_sigma: Dict[str, Tuple[float, float]]
) -> Dict[str, float]:
    """
    Calcula la probabilidad de congestión por recurso (CPU, RAM)
    si asignáramos el slice al host j.

    Usa:
    - CCLP (mu_host, sigma_host) existente
    - Suma normal DT = CCLP + Slice (medias y varianzas se suman)
    - P_cong,k = Q( (CI - mu_DT) / sigma_DT )
    
    NOTA: Disco NO se evalúa aquí porque es determinista
    """
    # 1) CPU
    mu_cpu_slice, sigma_cpu_slice = slice_mu_sigma["cpu"]
    mu_dt_cpu = host.mu_cpu + mu_cpu_slice
    sigma_dt_cpu = math.sqrt(host.sigma_cpu ** 2 + sigma_cpu_slice ** 2)
    p_cong_cpu = _normal_tail_probability(host.cpu_capacity, mu_dt_cpu, sigma_dt_cpu)

    # 2) RAM
    mu_ram_slice, sigma_ram_slice = slice_mu_sigma["ram"]
    mu_dt_ram = host.mu_ram_gb + mu_ram_slice
    sigma_dt_ram = math.sqrt(host.sigma_ram_gb ** 2 + sigma_ram_slice ** 2)
    p_cong_ram = _normal_tail_probability(host.ram_gb_capacity, mu_dt_ram, sigma_dt_ram)

    return {
        "cpu": p_cong_cpu,
        "ram": p_cong_ram,
    }


def compute_host_risk_current(host: HostState) -> float:
    """
    Riesgo actual del host j antes de asignar el nuevo slice:
    max_k P_cong,j,k (cuello de botella local).
    
    NOTA: Solo considera CPU y RAM (disco es determinista)
    """
    p_cpu = _normal_tail_probability(host.cpu_capacity, host.mu_cpu, host.sigma_cpu)
    p_ram = _normal_tail_probability(host.ram_gb_capacity, host.mu_ram_gb, host.sigma_ram_gb)
    return max(p_cpu, p_ram)


# ==========================
#   FUNCIÓN PRINCIPAL
# ==========================

def decide_vm_placement(
    slice_req: SliceRequest,
    hosts: List[HostState]
) -> Optional[PlacementDecision]:
    """
    Función principal del módulo de Placement (punto de entrada).

    - Recibe:
      * SliceRequest (CPU, RAM, Disco, zona, plataforma, perfil, contexto)
      * Lista de HostState (estado del clúster Linux + OpenStack)

    - Aplica:
      1) Filtro de viabilidad:
         a) Restricción DETERMINISTA de disco
         b) Probabilidad de congestión <= MP para CPU y RAM
      2) Criterio Minimax para balancear riesgo global del clúster

    - Retorna:
      * PlacementDecision (host elegido, plataforma, AZ y scheduler_hints si aplica)
      * None si no hay ningún host viable.
    """

    # 1. Interpretar requerimientos de usuario → obtener μ_slice,k y σ_slice,k
    #    (solo para CPU y RAM)
    slice_mu_sigma = compute_slice_mu_sigma(slice_req)

    # 2. Riesgo actual del clúster (antes de agregar el slice)
    baseline_risk = {h.name: compute_host_risk_current(h) for h in hosts}

    # 3. Filtrado de hosts según múltiples criterios
    candidates: List[Tuple[HostState, Dict[str, float]]] = []

    for h in hosts:
        # 3.1 Filtros básicos
        if not h.enabled or h.in_maintenance:
            continue

        if slice_req.zone and h.zone != slice_req.zone:
            continue

        if slice_req.platform in ("linux", "openstack") and h.platform != slice_req.platform:
            continue

        # 3.2 RESTRICCIÓN DETERMINISTA DE DISCO
        if not check_disk_constraint(h, slice_req.disk_gb):
            # No hay suficiente espacio en disco
            continue

        # 3.3 Calcular riesgo probabilístico tras asignar el slice (CPU y RAM)
        risks_after = compute_host_risk_after_assignment(h, slice_mu_sigma)

        # 3.4 Filtro de viabilidad probabilístico: 
        #     Todos los recursos (CPU, RAM) deben cumplir P_cong,k <= MP
        max_risk = max(risks_after.values())
        if max_risk > slice_req.max_failure_prob:
            # Host no viable (no cumple DTMP implícita)
            continue

        candidates.append((h, risks_after))

    if not candidates:
        # No hay host que cumpla todas las restricciones
        return None

    # 4. Criterio Minimax: elegir j* que minimiza el máximo riesgo global del clúster
    best_host: Optional[HostState] = None
    best_cluster_risk: Optional[float] = None
    best_host_risks: Optional[Dict[str, float]] = None

    for host, risks_after in candidates:
        # Riesgo local del host candidato después de la asignación
        local_max = max(risks_after.values())

        # Riesgo global: max entre todos los hosts
        cluster_max = 0.0
        for other_name, base_risk in baseline_risk.items():
            if other_name == host.name:
                cluster_max = max(cluster_max, local_max)
            else:
                cluster_max = max(cluster_max, base_risk)

        if best_cluster_risk is None or cluster_max < best_cluster_risk:
            best_cluster_risk = cluster_max
            best_host = host
            best_host_risks = risks_after

    if best_host is None:
        return None

    # 5. Construir decisión final distinta para Linux vs OpenStack
    if best_host.platform == "linux":
        # Para Linux devolvemos simplemente el host físico, el orquestador
        # es el que creará las VMs en ese nodo KVM.
        return PlacementDecision(
            host=best_host.name,
            platform="linux",
            availability_zone=best_host.zone,
            scheduler_hints={},
            reason=f"Host Linux seleccionado con riesgo máximo {max(best_host_risks.values()):.4f}"
        )

    else:  # OpenStack
        # En OpenStack se debe usar Availability Zones como mecanismo principal de enforcement.
        # Además podemos usar scheduler_hints para forzar el host si el orquestador así lo requiere.
        hints = {
            "availability_zone": best_host.zone,
            "force_hosts": best_host.name  # si quieren fijar el host exacto
        }
        return PlacementDecision(
            host=best_host.name,
            platform="openstack",
            availability_zone=best_host.zone,
            scheduler_hints=hints,
            reason=f"Host OpenStack en AZ {best_host.zone} seleccionado con riesgo máximo {max(best_host_risks.values()):.4f}"
        )