# 🚀 Inicio Rápido - Resources API

## Pasos para iniciar el microservicio

### 1. Iniciar todos los servicios
```bash
cd /home/ubuntu/proyecto_cloud
docker-compose up -d
```

### 2. Verificar que los contenedores estén corriendo
```bash
docker-compose ps
```

Deberías ver 4 contenedores:
- `orchestrator_api` (puerto 8000)
- `orchestrator_db` (puerto 3307)
- `orchestrator_pma` (puerto 8080)
- `resources_api` (puerto 8001) ⭐

### 3. Ver logs del microservicio
```bash
docker-compose logs -f resources_api
```

### 4. Verificar que la API esté funcionando
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

### 5. Explorar la documentación interactiva
Abre en tu navegador: **http://localhost:8001/docs**

## 🧪 Ejecutar pruebas

### Opción 1: Script de Python
```bash
# Instalar requests si no lo tienes
pip install requests

# Ejecutar pruebas
cd /home/ubuntu/proyecto_cloud/resources_api
python test_api.py
```

### Opción 2: Script con cURL
```bash
cd /home/ubuntu/proyecto_cloud/resources_api
bash examples.sh
```

## 📊 Revisar datos en la base de datos

### Opción 1: phpMyAdmin
1. Abre: **http://localhost:8080**
2. Usuario: `orch`
3. Contraseña: `orchpass`
4. Navega a la tabla `vlans` o `vnc_ports`

### Opción 2: MySQL CLI
```bash
docker exec -it orchestrator_db mysql -uorch -porchpass orchestrator
```

Luego ejecuta:
```sql
-- Ver VLANs disponibles
SELECT * FROM vlans WHERE is_used = 0 LIMIT 10;

-- Ver puertos VNC disponibles
SELECT * FROM vnc_ports WHERE is_used = 0 LIMIT 10;

-- Ver VLANs en uso
SELECT * FROM vlans WHERE is_used = 1;
```

## 🔄 Reiniciar servicios

### Reiniciar solo el microservicio de recursos
```bash
docker-compose restart resources_api
```

### Reconstruir después de cambios en el código
```bash
docker-compose up -d --build resources_api
```

### Reiniciar todo
```bash
docker-compose restart
```

## 🛑 Detener servicios

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO! Borra la BD)
docker-compose down -v
```

## 📡 Endpoints principales

### VLANs
- `GET http://localhost:8001/api/v1/vlans/available` - VLANs disponibles
- `POST http://localhost:8001/api/v1/vlans/reserve` - Reservar VLAN
- `POST http://localhost:8001/api/v1/vlans/release` - Liberar VLAN

### Puertos VNC
- `GET http://localhost:8001/api/v1/vnc-ports/available` - Puertos disponibles
- `POST http://localhost:8001/api/v1/vnc-ports/reserve` - Reservar puerto
- `POST http://localhost:8001/api/v1/vnc-ports/release` - Liberar puerto

## 🐛 Solución de problemas

### Error: "Connection refused"
```bash
# Verificar que el contenedor esté corriendo
docker-compose ps resources_api

# Ver logs para identificar el error
docker-compose logs resources_api
```

### Error: "Can't connect to MySQL server"
```bash
# Verificar que la BD esté corriendo
docker-compose ps db

# Esperar unos segundos a que la BD inicie completamente
# Luego reiniciar el microservicio
docker-compose restart resources_api
```

### Los cambios no se reflejan
```bash
# Reconstruir la imagen
docker-compose up -d --build resources_api
```

## 📚 Documentación adicional
- [README completo](./README.md)
- [Documentación Swagger](http://localhost:8001/docs)
- [Documentación ReDoc](http://localhost:8001/redoc)
