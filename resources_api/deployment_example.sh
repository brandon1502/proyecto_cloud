#!/bin/bash

# Script de ejemplo para usar la API de Slices
# Simula el flujo de deployment desde otro servidor

API_HOST="10.20.12.26"
API_PORT="8001"
BASE_URL="http://${API_HOST}:${API_PORT}/api/v1"

echo "🚀 Simulando Deployment de Slice"
echo "=================================="

# 1. Obtener VLAN disponible
echo -e "\n📡 1. Obteniendo VLAN disponible..."
VLAN_RESPONSE=$(curl -s "${BASE_URL}/vlans/available?limit=1")
VLAN_ID=$(echo $VLAN_RESPONSE | jq -r '.[0].vlan_id')
VLAN_NUMBER=$(echo $VLAN_RESPONSE | jq -r '.[0].vlan_number')
echo "   VLAN obtenida: ID=$VLAN_ID, Number=$VLAN_NUMBER"

# 2. Obtener puertos VNC disponibles
echo -e "\n🖥️  2. Obteniendo 3 puertos VNC disponibles..."
VNC_RESPONSE=$(curl -s "${BASE_URL}/vnc-ports/available?limit=3")
echo "   Puertos VNC obtenidos:"
echo $VNC_RESPONSE | jq -r '.[] | "   - Puerto \(.port_number) (ID: \(.vnc_port_id))"'

# 3. Simular deployment en OpenStack/otro sistema
echo -e "\n⚙️  3. Desplegando en OpenStack..."
echo "   [Simulación] Creando VMs..."
echo "   [Simulación] Configurando red..."
echo "   [Simulación] Asignando IPs..."
sleep 2
echo "   ✅ Deployment exitoso!"

# 4. DESPUÉS del deployment exitoso, guardar en BD
echo -e "\n💾 4. Guardando slice en base de datos..."
SLICE_RESPONSE=$(curl -s -X POST "${BASE_URL}/slices/" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": 1,
    "name": "Slice de Producción",
    "az_id": 1,
    "template_id": 1,
    "status": "active",
    "placement_strategy": "distributed",
    "sla_overcommit_cpu_pct": 1.5,
    "sla_overcommit_ram_pct": 1.2,
    "internet_egress": true,
    "created_by": 1
  }')

SLICE_ID=$(echo $SLICE_RESPONSE | jq -r '.slice_id')
echo "   ✅ Slice guardado con ID: $SLICE_ID"
echo $SLICE_RESPONSE | jq '.'

# 5. Reservar VLAN para el slice
echo -e "\n🔒 5. Reservando VLAN $VLAN_NUMBER para slice $SLICE_ID..."
curl -s -X POST "${BASE_URL}/vlans/reserve" \
  -H "Content-Type: application/json" \
  -d "{
    \"vlan_id\": $VLAN_ID,
    \"slice_id\": $SLICE_ID,
    \"reserved_by\": 1,
    \"description\": \"VLAN para slice $SLICE_ID\"
  }" | jq '.'

# 6. Reservar puertos VNC para las VMs
echo -e "\n🔒 6. Reservando puertos VNC para las VMs del slice..."
VNC_PORT_IDS=$(echo $VNC_RESPONSE | jq -r '.[].vnc_port_id')
VM_ID=1
for PORT_ID in $VNC_PORT_IDS; do
  echo "   Reservando puerto VNC ID=$PORT_ID para VM $VM_ID..."
  curl -s -X POST "${BASE_URL}/vnc-ports/reserve" \
    -H "Content-Type: application/json" \
    -d "{
      \"vnc_port_id\": $PORT_ID,
      \"vm_id\": $VM_ID,
      \"slice_id\": $SLICE_ID,
      \"reserved_by\": 1,
      \"description\": \"Puerto VNC para VM $VM_ID del slice $SLICE_ID\"
    }" > /dev/null
  VM_ID=$((VM_ID + 1))
done
echo "   ✅ Puertos VNC reservados"

# 7. Consultar slice creado
echo -e "\n📋 7. Consultando slice creado..."
curl -s "${BASE_URL}/slices/$SLICE_ID" | jq '.'

# 8. Actualizar estado del slice
echo -e "\n🔄 8. Actualizando estado del slice a 'running'..."
curl -s -X PUT "${BASE_URL}/slices/$SLICE_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "updated_by": 1
  }' | jq '.'

echo -e "\n✅ Proceso de deployment completo!"
echo "=================================="
echo "Slice ID: $SLICE_ID"
echo "VLAN reservada: $VLAN_NUMBER"
echo "Estado: running"
