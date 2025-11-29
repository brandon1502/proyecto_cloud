#!/bin/bash
# Ejemplos de uso de la Resources API con cURL
# Asegúrate de que los contenedores estén corriendo: docker-compose up -d

BASE_URL="http://localhost:8001/api/v1"

echo "=============================================="
echo "Resources API - Ejemplos de uso con cURL"
echo "=============================================="

# Health Check
echo -e "\n📊 Health Check:"
curl -s http://localhost:8001/health | jq

echo -e "\n\n=============================================="
echo "🔷 VLAN Endpoints"
echo "=============================================="

# 1. Obtener VLANs disponibles
echo -e "\n1️⃣  Obtener VLANs disponibles (primeras 5):"
curl -s "${BASE_URL}/vlans/available?limit=5" | jq

# 2. Listar todas las VLANs
echo -e "\n2️⃣  Listar todas las VLANs:"
curl -s "${BASE_URL}/vlans?limit=10" | jq

# 3. Obtener VLAN específica
echo -e "\n3️⃣  Obtener VLAN con ID 1:"
curl -s "${BASE_URL}/vlans/1" | jq

# 4. Crear nueva VLAN
echo -e "\n4️⃣  Crear nueva VLAN (número 500):"
curl -s -X POST "${BASE_URL}/vlans" \
  -H "Content-Type: application/json" \
  -d '{
    "vlan_number": 500,
    "description": "VLAN de prueba desde cURL"
  }' | jq

# 5. Reservar VLAN
echo -e "\n5️⃣  Reservar VLAN ID 5:"
curl -s -X POST "${BASE_URL}/vlans/reserve" \
  -H "Content-Type: application/json" \
  -d '{
    "vlan_id": 5,
    "slice_id": 10,
    "reserved_by": 1,
    "description": "Reservada para deployment de producción"
  }' | jq

# 6. Liberar VLAN
echo -e "\n6️⃣  Liberar VLAN ID 5:"
curl -s -X POST "${BASE_URL}/vlans/release" \
  -H "Content-Type: application/json" \
  -d '{
    "vlan_id": 5
  }' | jq

echo -e "\n\n=============================================="
echo "🖥️  VNC Port Endpoints"
echo "=============================================="

# 7. Obtener puertos VNC disponibles
echo -e "\n7️⃣  Obtener puertos VNC disponibles (primeros 5):"
curl -s "${BASE_URL}/vnc-ports/available?limit=5" | jq

# 8. Listar todos los puertos VNC
echo -e "\n8️⃣  Listar todos los puertos VNC:"
curl -s "${BASE_URL}/vnc-ports?limit=10" | jq

# 9. Obtener puerto VNC específico
echo -e "\n9️⃣  Obtener puerto VNC con ID 1:"
curl -s "${BASE_URL}/vnc-ports/1" | jq

# 10. Crear nuevo puerto VNC
echo -e "\n🔟 Crear nuevo puerto VNC (6001):"
curl -s -X POST "${BASE_URL}/vnc-ports" \
  -H "Content-Type: application/json" \
  -d '{
    "port_number": 6001,
    "description": "Puerto VNC de prueba desde cURL"
  }' | jq

# 11. Reservar puerto VNC
echo -e "\n1️⃣1️⃣  Reservar puerto VNC ID 10:"
curl -s -X POST "${BASE_URL}/vnc-ports/reserve" \
  -H "Content-Type: application/json" \
  -d '{
    "vnc_port_id": 10,
    "vm_id": 42,
    "slice_id": 10,
    "reserved_by": 1,
    "description": "Puerto para VM web-server-01"
  }' | jq

# 12. Liberar puerto VNC
echo -e "\n1️⃣2️⃣  Liberar puerto VNC ID 10:"
curl -s -X POST "${BASE_URL}/vnc-ports/release" \
  -H "Content-Type: application/json" \
  -d '{
    "vnc_port_id": 10
  }' | jq

echo -e "\n\n=============================================="
echo "🔍 Búsquedas con Filtros"
echo "=============================================="

# 13. VLANs por estado
echo -e "\n1️⃣3️⃣  VLANs en uso:"
curl -s "${BASE_URL}/vlans?is_used=true&limit=5" | jq

echo -e "\n1️⃣4️⃣  VLANs disponibles:"
curl -s "${BASE_URL}/vlans?is_used=false&limit=5" | jq

# 15. Puertos VNC por VM
echo -e "\n1️⃣5️⃣  Puertos VNC de la VM ID 42:"
curl -s "${BASE_URL}/vnc-ports?vm_id=42" | jq

echo -e "\n\n=============================================="
echo "✅ Ejemplos completados"
echo "=============================================="
echo ""
echo "📚 Para ver la documentación interactiva:"
echo "   http://localhost:8001/docs"
echo ""
