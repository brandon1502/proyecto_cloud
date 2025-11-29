# Resources API - Microservicio de Gestión de Recursos

API RESTful para gestionar recursos del orquestador: VLANs y puertos VNC.

## 🚀 Características

- **Gestión de VLANs**: Consultar, reservar y liberar VLANs para slices
- **Gestión de Puertos VNC**: Consultar, reservar y liberar puertos VNC para VMs
- **Arquitectura de Microservicio**: Contenedor Docker independiente
- **Base de datos compartida**: Conecta a la misma BD que el orquestador principal
- **API RESTful**: Documentación automática con Swagger/OpenAPI

## 📋 Endpoints Principales

### VLANs

#### Obtener VLANs disponibles
```bash
GET /api/v1/vlans/available?az_id=1&limit=10
```

#### Listar todas las VLANs
```bash
GET /api/v1/vlans?is_used=false&az_id=1&limit=100&offset=0
```

#### Obtener VLAN específica
```bash
GET /api/v1/vlans/{vlan_id}
```

#### Crear nueva VLAN
```bash
POST /api/v1/vlans
Content-Type: application/json

{
  "vlan_number": 200,
  "az_id": 1,
  "description": "VLAN para proyecto X"
}
```

#### Reservar VLAN
```bash
POST /api/v1/vlans/reserve
Content-Type: application/json

{
  "vlan_id": 5,
  "slice_id": 10,
  "reserved_by": 2,
  "description": "Reservada para slice de producción"
}
```

#### Liberar VLAN
```bash
POST /api/v1/vlans/release
Content-Type: application/json

{
  "vlan_id": 5
}
```

#### Eliminar VLAN
```bash
DELETE /api/v1/vlans/{vlan_id}
```

### Puertos VNC

#### Obtener puertos VNC disponibles
```bash
GET /api/v1/vnc-ports/available?az_id=1&limit=10
```

#### Listar todos los puertos VNC
```bash
GET /api/v1/vnc-ports?is_used=false&vm_id=5&limit=100&offset=0
```

#### Obtener puerto VNC específico
```bash
GET /api/v1/vnc-ports/{vnc_port_id}
```

#### Crear nuevo puerto VNC
```bash
POST /api/v1/vnc-ports
Content-Type: application/json

{
  "port_number": 5999,
  "az_id": 1,
  "description": "Puerto VNC personalizado"
}
```

#### Reservar puerto VNC
```bash
POST /api/v1/vnc-ports/reserve
Content-Type: application/json

{
  "vnc_port_id": 15,
  "vm_id": 42,
  "slice_id": 10,
  "reserved_by": 2,
  "description": "Puerto para VM de desarrollo"
}
```

#### Liberar puerto VNC
```bash
POST /api/v1/vnc-ports/release
Content-Type: application/json

{
  "vnc_port_id": 15
}
```

#### Eliminar puerto VNC
```bash
DELETE /api/v1/vnc-ports/{vnc_port_id}
```

## 🐳 Deployment con Docker

### Iniciar el microservicio

```bash
# Desde el directorio proyecto_cloud
docker-compose up -d resources_api
```

### Ver logs
```bash
docker-compose logs -f resources_api
```

### Reiniciar el servicio
```bash
docker-compose restart resources_api
```

### Reconstruir después de cambios
```bash
docker-compose up -d --build resources_api
```

## 🌐 Acceso a la API

- **URL Base**: `http://localhost:8001`
- **Documentación Swagger**: `http://localhost:8001/docs`
- **Documentación ReDoc**: `http://localhost:8001/redoc`
- **Health Check**: `http://localhost:8001/health`

## 🗄️ Estructura de la Base de Datos

### Tabla: `vlans`
```sql
- vlan_id (BIGINT, PK)
- vlan_number (INT) - Número de VLAN (1-4094)
- az_id (BIGINT, FK) - Zona de disponibilidad
- is_used (BOOLEAN) - 0 = disponible, 1 = en uso
- slice_id (BIGINT, FK) - Slice que usa la VLAN
- description (VARCHAR)
- reserved_at (TIMESTAMP)
- reserved_by (BIGINT, FK) - Usuario que reservó
- released_at (TIMESTAMP)
- created_at (TIMESTAMP)
```

### Tabla: `vnc_ports`
```sql
- vnc_port_id (BIGINT, PK)
- port_number (INT) - Número de puerto VNC
- az_id (BIGINT, FK) - Zona de disponibilidad
- is_used (BOOLEAN) - 0 = disponible, 1 = en uso
- vm_id (BIGINT, FK) - VM que usa el puerto
- slice_id (BIGINT, FK) - Slice asociado
- description (VARCHAR)
- reserved_at (TIMESTAMP)
- reserved_by (BIGINT, FK) - Usuario que reservó
- released_at (TIMESTAMP)
- created_at (TIMESTAMP)
```

## 📦 Datos Iniciales

Al inicializar la base de datos, se crean automáticamente:
- **31 VLANs**: Números 100-130
- **51 Puertos VNC**: Números 5900-5950

## 🔧 Variables de Entorno

```env
DB_HOST=db
DB_PORT=3306
DB_USER=orch
DB_PASSWORD=orchpass
DB_NAME=orchestrator
```

## 📝 Ejemplos de Uso

### Flujo típico para deployment de slice:

1. **Obtener VLAN disponible**
```bash
curl http://localhost:8001/api/v1/vlans/available?limit=1
```

2. **Reservar VLAN**
```bash
curl -X POST http://localhost:8001/api/v1/vlans/reserve \
  -H "Content-Type: application/json" \
  -d '{"vlan_id": 1, "slice_id": 5, "reserved_by": 2}'
```

3. **Obtener puertos VNC para VMs**
```bash
curl http://localhost:8001/api/v1/vnc-ports/available?limit=3
```

4. **Reservar puerto VNC para cada VM**
```bash
curl -X POST http://localhost:8001/api/v1/vnc-ports/reserve \
  -H "Content-Type: application/json" \
  -d '{"vnc_port_id": 10, "vm_id": 42, "slice_id": 5}'
```

### Flujo de limpieza al eliminar slice:

1. **Liberar VLAN**
```bash
curl -X POST http://localhost:8001/api/v1/vlans/release \
  -H "Content-Type: application/json" \
  -d '{"vlan_id": 1}'
```

2. **Liberar puertos VNC**
```bash
curl -X POST http://localhost:8001/api/v1/vnc-ports/release \
  -H "Content-Type: application/json" \
  -d '{"vnc_port_id": 10}'
```

## 🔐 Seguridad

⚠️ **IMPORTANTE para producción**:
- Implementar autenticación (JWT, API Keys)
- Configurar CORS específicos (no usar `allow_origins=["*"]`)
- Usar HTTPS
- Validar permisos de usuarios
- Rate limiting

## 🛠️ Desarrollo

### Estructura del proyecto
```
resources_api/
├── __init__.py
├── main.py              # Aplicación FastAPI principal
├── database.py          # Configuración de SQLAlchemy
├── models.py            # Modelos de BD
├── schemas.py           # Schemas Pydantic
├── Dockerfile
├── requirements.txt
└── routes/
    ├── __init__.py
    ├── vlans.py         # Endpoints de VLANs
    └── vnc_ports.py     # Endpoints de puertos VNC
```

### Agregar nuevos endpoints

1. Crear nueva ruta en `routes/`
2. Importar en `main.py`
3. Registrar router:
```python
app.include_router(nuevo_router, prefix="/api/v1/nuevo", tags=["Nuevo"])
```

## 📊 Monitoreo

Ver estado del servicio:
```bash
curl http://localhost:8001/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 🐛 Troubleshooting

### Error de conexión a BD
```bash
# Verificar que el contenedor de BD esté corriendo
docker-compose ps db

# Ver logs de la BD
docker-compose logs db
```

### Puerto 8001 ya en uso
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8002:8001"  # Usar puerto 8002 externamente
```

### Reconstruir desde cero
```bash
docker-compose down -v
docker-compose up -d --build
```

## 📄 Licencia

Proyecto interno del orquestador.
