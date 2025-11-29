#!/bin/bash
# Script para limpiar todos los recursos de deployments fallidos usando la API

echo "🧹 Limpiando recursos de deployments fallidos..."
echo ""

# Llamar a la API de limpieza
response=$(curl -s -X POST http://localhost:8001/api/v1/cleanup/all)

# Mostrar resultado
echo "📋 Resultado de la limpieza:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

echo ""
echo "📊 Estado actual de recursos:"
echo ""

docker exec orchestrator_db mysql -uorch -porchpass orchestrator -e "
SELECT 'VLANs disponibles' as Recurso, COUNT(*) as Cantidad FROM vlans WHERE is_used = 0
UNION ALL SELECT 'VLANs en uso', COUNT(*) FROM vlans WHERE is_used = 1
UNION ALL SELECT 'VNC ports disponibles', COUNT(*) FROM vnc_ports WHERE is_used = 0
UNION ALL SELECT 'VNC ports en uso', COUNT(*) FROM vnc_ports WHERE is_used = 1
UNION ALL SELECT 'Slices activos', COUNT(*) FROM slices WHERE status = 'active'
UNION ALL SELECT 'Slices fallidos', COUNT(*) FROM slices WHERE status IN ('failed', 'error')
UNION ALL SELECT 'VMs totales', COUNT(*) FROM vms;
" 2>/dev/null

echo ""
echo "🚀 Listo para deployar!"
