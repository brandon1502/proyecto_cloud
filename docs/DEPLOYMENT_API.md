# API de Despliegue - Documentación

## Servidor de Despliegue

**Ubicación**: `http://10.20.12.209:5814`  
**Endpoint**: `/api/deploy`  
**Método**: `POST`

## Formato del JSON Enviado

Cuando el usuario hace clic en "Desplegar" en el modal de zonas de disponibilidad, se envía un POST con el siguiente formato:

```json
{
  "requester_user_id": 123,
  "requester_username": "brandon",
  "requester_email": "brandon@example.com",
  "name": "Mi-Topologia-20251108143022",
  "zone": "zone1",
  "template_id": 456,
  "topology": {
    "topologia": {
      "nodes": [
        {
          "id": "vm-1",
          "label": "VM-001",
          "shape": "image",
          "image": "/static/images/pc.png"
        },
        {
          "id": "vm-2",
          "label": "VM-002",
          "shape": "image",
          "image": "/static/images/pc.png"
        }
      ],
      "edges": [
        {
          "id": "edge-vm-1-vm-2",
          "from": "vm-1",
          "to": "vm-2"
        }
      ]
    },
    "recursos": {
      "vm-1": {
        "name": "VM-001",
        "ram_gb": 4.0,
        "vcpu": 2,
        "disk_gb": 6.0,
        "os": "ubuntu",
        "flavour": "small"
      },
      "vm-2": {
        "name": "VM-002",
        "ram_gb": 2.0,
        "vcpu": 2,
        "disk_gb": 4.0,
        "os": "ubuntu",
        "flavour": "micro"
      }
    },
    "subred": {
      "public_access": ["vm-1"]
    }
  }
}
```

## Estructura Detallada

### Campos Raíz

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `requester_user_id` | int | ID del usuario que solicita el despliegue |
| `requester_username` | string | Nombre de usuario |
| `requester_email` | string | Email del usuario |
| `name` | string | Nombre del despliegue (formato: `<plantilla>-YYYYMMDDHHMMSS`) |
| `zone` | string | Zona de disponibilidad seleccionada (zone1, zone2, zone3) |
| `template_id` | int | ID de la plantilla en la base de datos |
| `topology` | object | Objeto completo con la topología |

### Estructura de `topology`

#### `topology.topologia.nodes` (array)
Lista de VMs a desplegar:
- **id**: Identificador único (ej: "vm-1", "vm-2")
- **label**: Etiqueta visible (ej: "VM-001")
- **shape**: Siempre "image"
- **image**: Ruta de la imagen (para UI)

#### `topology.topologia.edges` (array)
Conexiones entre VMs:
- **id**: Identificador de la conexión
- **from**: ID del nodo origen
- **to**: ID del nodo destino

#### `topology.recursos` (object)
Diccionario con recursos de cada VM:

| Campo | Tipo | Valores | Descripción |
|-------|------|---------|-------------|
| `name` | string | - | Nombre de la VM |
| `ram_gb` | float | 1, 2, 4, 8, 12, 16 | RAM en GB |
| `vcpu` | int | 1, 2, 4, 8, 16 | Número de vCPUs |
| `disk_gb` | float | 2, 3, 4, 6, 8, 10, 12 | Disco en GB |
| `os` | string | ubuntu, centos, debian, cirros | Sistema operativo |
| `flavour` | string | nano, mini, micro, small, medium, large, xlarge | Tipo de flavour |

#### `topology.subred.public_access` (array)
Lista de IDs de VMs que requieren acceso público a Internet.

## Flavours Disponibles

| Flavour | vCPU | RAM (GB) | Disco (GB) |
|---------|------|----------|------------|
| nano    | 1    | 1        | 2          |
| mini    | 1    | 2        | 3          |
| micro   | 2    | 2        | 4          |
| small   | 2    | 4        | 6          |
| medium  | 4    | 8        | 8          |
| large   | 8    | 12       | 10         |
| xlarge  | 16   | 16       | 12         |

## Respuesta Esperada

El servidor de despliegue debe responder con un JSON:

### Respuesta Exitosa (200 OK)
```json
{
  "success": true,
  "job_id": "deploy-abc123xyz",
  "deployment_id": "xyz-789",
  "status": "ACCEPTED",
  "message": "Despliegue aceptado y en proceso"
}
```

### Respuesta de Error (4xx/5xx)
```json
{
  "detail": "Descripción del error",
  "error": "mensaje de error alternativo"
}
```

## Implementación Recomendada en Server4

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI()

class TopologyNode(BaseModel):
    id: str
    label: str
    shape: str
    image: str

class TopologyEdge(BaseModel):
    id: str
    from_: str = Field(alias="from")
    to: str

class VMResource(BaseModel):
    name: str
    ram_gb: float
    vcpu: int
    disk_gb: float
    os: str
    flavour: str

class Topology(BaseModel):
    topologia: Dict
    recursos: Dict[str, VMResource]
    subred: Dict

class DeploymentRequest(BaseModel):
    requester_user_id: int
    requester_username: str
    requester_email: str
    name: str
    zone: str
    template_id: int
    topology: Topology

@app.post("/api/deploy")
async def deploy(request: DeploymentRequest):
    try:
        # Aquí va el código de tu amigo para desplegar
        # Ejemplo de acceso a los datos:
        print(f"Usuario: {request.requester_username}")
        print(f"Zona: {request.zone}")
        print(f"VMs a crear: {len(request.topology.recursos)}")
        
        # Iterar sobre las VMs
        for vm_id, vm_config in request.topology.recursos.items():
            print(f"VM {vm_id}: {vm_config.name} - {vm_config.flavour}")
            # Aquí llamar a las funciones de despliegue de tu amigo
            # create_vm(vm_config.name, vm_config.vcpu, vm_config.ram_gb, ...)
        
        # Iterar sobre las conexiones
        for edge in request.topology.topologia["edges"]:
            print(f"Conexión: {edge['from']} -> {edge['to']}")
            # Aquí configurar las redes entre VMs
        
        # Configurar acceso público
        public_vms = request.topology.subred.get("public_access", [])
        for vm_id in public_vms:
            print(f"VM {vm_id} requiere acceso público")
        
        # Retornar respuesta exitosa
        return {
            "success": True,
            "job_id": "deploy-" + str(uuid.uuid4())[:8],
            "status": "ACCEPTED",
            "message": "Despliegue iniciado correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Flujo Completo del Despliegue

1. **Usuario crea plantilla** → Se guarda en BD con `json_template`
2. **Usuario va a "Proyectos"** → Presiona "Desplegar plantilla"
3. **Selecciona plantilla y zona** → Presiona "Desplegar"
4. **Frontend llama a `/deployments/trigger`** → Tu backend
5. **Tu backend envía POST a `10.20.12.209:5814/api/deploy`** → Server4
6. **Server4 ejecuta código de despliegue** → Crea VMs en Linux
7. **Server4 responde con job_id** → Tu backend lo pasa al frontend
8. **Frontend guarda en `/slices`** → Crea registro del proyecto
9. **Usuario ve el proyecto en la tabla** → Con estado PENDING/RUNNING

## Manejo de Errores

### En tu aplicación
- Timeout (30s): Retorna HTTP 504
- Error de conexión: Retorna HTTP 503
- Error del servidor de despliegue: Retorna HTTP 502

### En el servidor de despliegue (Server4)
- Recursos insuficientes: HTTP 400 + detail
- Error interno: HTTP 500 + detail
- Zona no válida: HTTP 400 + detail

## Testing

Puedes probar manualmente con curl:

```bash
curl -X POST http://10.20.12.209:5814/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "requester_user_id": 1,
    "requester_username": "test",
    "requester_email": "test@test.com",
    "name": "Test-20251108",
    "zone": "zone1",
    "template_id": 1,
    "topology": {
      "topologia": {
        "nodes": [{"id": "vm-1", "label": "VM-001", "shape": "image", "image": "/pc.png"}],
        "edges": []
      },
      "recursos": {
        "vm-1": {
          "name": "VM-001",
          "ram_gb": 4.0,
          "vcpu": 2,
          "disk_gb": 6.0,
          "os": "ubuntu",
          "flavour": "small"
        }
      },
      "subred": {"public_access": []}
    }
  }'
```

## Notas Importantes

- El timeout de conexión es de 30 segundos
- El nombre del despliegue se genera automáticamente con timestamp
- Las zonas de disponibilidad son solo referencia (zone1, zone2, zone3)
- El campo `public_access` indica qué VMs necesitan IP pública
- Todos los valores de recursos (RAM, disco) son números enteros
