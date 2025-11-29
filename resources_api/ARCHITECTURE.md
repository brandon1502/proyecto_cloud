# 🏗️ Arquitectura del Sistema

## Diagrama de Servicios

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Compose Network                      │
│                          (backend)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │  orchestrator_api│      │  resources_api   │                │
│  │                  │      │                  │                │
│  │  FastAPI         │      │  FastAPI         │                │
│  │  Port: 8000      │      │  Port: 8001  ⭐  │                │
│  │                  │      │                  │                │
│  │  - Auth          │      │  - VLANs API     │                │
│  │  - Deployments   │      │  - VNC Ports API │                │
│  │  - Templates     │      │                  │                │
│  │  - Slices        │      │                  │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                          │
│           │                         │                          │
│           └──────────┬──────────────┘                          │
│                      │                                         │
│                      ▼                                         │
│           ┌──────────────────────┐                             │
│           │  orchestrator_db     │                             │
│           │                      │                             │
│           │  MySQL 8.0           │                             │
│           │  Port: 3307          │                             │
│           │                      │                             │
│           │  Tables:             │                             │
│           │  - users             │                             │
│           │  - slices            │                             │
│           │  - vms               │                             │
│           │  - vlans         ⭐  │                             │
│           │  - vnc_ports     ⭐  │                             │
│           │  - templates         │                             │
│           │  - ...               │                             │
│           └──────────┬───────────┘                             │
│                      │                                         │
│                      ▼                                         │
│           ┌──────────────────────┐                             │
│           │  orchestrator_pma    │                             │
│           │                      │                             │
│           │  phpMyAdmin          │                             │
│           │  Port: 8080          │                             │
│           │                      │                             │
│           │  (Web UI para DB)    │                             │
│           └──────────────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos - Deployment de Slice

```
1. Usuario crea slice
   │
   ▼
2. orchestrator_api
   │
   ├─► GET resources_api/vlans/available
   │   └─► Obtiene VLAN disponible
   │
   ├─► POST resources_api/vlans/reserve
   │   └─► Reserva VLAN para el slice
   │
   ├─► GET resources_api/vnc-ports/available?limit=N
   │   └─► Obtiene N puertos VNC (uno por VM)
   │
   ├─► POST resources_api/vnc-ports/reserve (por cada VM)
   │   └─► Reserva puerto VNC para la VM
   │
   └─► Continúa con deployment en OpenStack
```

## Flujo de Datos - Eliminación de Slice

```
1. Usuario elimina slice
   │
   ▼
2. orchestrator_api
   │
   ├─► Elimina VMs en OpenStack
   │
   ├─► POST resources_api/vnc-ports/release (por cada VM)
   │   └─► Libera puertos VNC
   │
   ├─► POST resources_api/vlans/release
   │   └─► Libera VLAN del slice
   │
   └─► Elimina slice de BD
```

## Endpoints por Servicio

### orchestrator_api (Puerto 8000)
```
/auth/*              - Autenticación y autorización
/deployments/*       - Gestión de deployments
/templates/*         - Plantillas de topología
/slices/*            - Gestión de slices
/flavours/*          - Sabores de VMs
```

### resources_api (Puerto 8001) ⭐ NUEVO
```
/api/v1/vlans/*      - Gestión de VLANs
/api/v1/vnc-ports/*  - Gestión de puertos VNC
```

### phpMyAdmin (Puerto 8080)
```
/                    - Interfaz web para MySQL
```

## Tablas de Base de Datos

### Nuevas Tablas ⭐

#### `vlans`
```sql
vlan_id          BIGINT (PK)
vlan_number      INT
az_id            BIGINT (FK → availability_zones)
is_used          BOOLEAN (0=disponible, 1=en uso)
slice_id         BIGINT (FK → slices)
description      VARCHAR(255)
reserved_at      TIMESTAMP
reserved_by      BIGINT (FK → users)
released_at      TIMESTAMP
created_at       TIMESTAMP
```

#### `vnc_ports`
```sql
vnc_port_id      BIGINT (PK)
port_number      INT
az_id            BIGINT (FK → availability_zones)
is_used          BOOLEAN (0=disponible, 1=en uso)
vm_id            BIGINT (FK → vms)
slice_id         BIGINT (FK → slices)
description      VARCHAR(255)
reserved_at      TIMESTAMP
reserved_by      BIGINT (FK → users)
released_at      TIMESTAMP
created_at       TIMESTAMP
```

## URLs de Acceso

| Servicio | URL | Propósito |
|----------|-----|-----------|
| **Orchestrator API** | http://localhost:8000 | API principal |
| **Orchestrator Docs** | http://localhost:8000/docs | Documentación Swagger |
| **Resources API** ⭐ | http://localhost:8001 | API de recursos |
| **Resources Docs** ⭐ | http://localhost:8001/docs | Documentación Swagger |
| **phpMyAdmin** | http://localhost:8080 | Admin de BD |
| **MySQL (externo)** | localhost:3307 | Conexión directa a BD |

## Seguridad

### Red Interna (backend)
- Todos los servicios están en la misma red Docker
- Comunicación interna por nombres de servicio (ej: `db`, `resources_api`)

### Puertos Expuestos
- **8000**: orchestrator_api (público)
- **8001**: resources_api (público) ⭐
- **8080**: phpMyAdmin (desarrollo)
- **3307**: MySQL (desarrollo - NO exponer en producción)

### Variables de Entorno
```bash
DB_HOST=db
DB_PORT=3306
DB_USER=orch
DB_PASSWORD=orchpass
DB_NAME=orchestrator
```

## Datos Iniciales

Al inicializar la base de datos:
- ✅ 31 VLANs (100-130)
- ✅ 51 Puertos VNC (5900-5950)
- ✅ Usuarios y roles
- ✅ Flavours de VM

## Escalabilidad

### Horizontal
- Agregar más instancias de `resources_api` con load balancer
- Usar pool de conexiones a BD

### Vertical
- Aumentar recursos de contenedores en `docker-compose.yml`

## Monitoreo

```bash
# Estado de servicios
docker-compose ps

# Logs en tiempo real
docker-compose logs -f resources_api

# Uso de recursos
docker stats
```
