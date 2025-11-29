#!/bin/bash
# Script para configurar reglas iptables en el GATEWAY (10.20.12.209)
# Redirige puertos externos a websockify en los servers internos

echo "🔧 Configurando reglas iptables para acceso VNC..."
echo "⚠️  EJECUTAR ESTE SCRIPT EN EL GATEWAY (10.20.12.209)"

# Habilitar IP forwarding (necesario para NAT)
echo "📡 Habilitando IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# Crear reglas DNAT para redirigir puertos
# Formato: Puerto externo en gateway → Server interno:Puerto WebSocket
# Usamos rango 7000-7100 para los puertos externos

echo "🔀 Creando reglas DNAT..."

# Server 1 (10.20.201.1) - Puertos WebSocket 6000-6050
for vnc_port in {5900..5950}; do
    ws_port=$((6000 + vnc_port - 5900))
    external_port=$((7000 + vnc_port - 5900))
    
    # PREROUTING: Cambiar destino de paquetes entrantes
    sudo iptables -t nat -A PREROUTING -p tcp --dport $external_port -j DNAT --to-destination 10.20.201.1:$ws_port
    
    # POSTROUTING: Masquerade para que las respuestas vuelvan por el gateway
    sudo iptables -t nat -A POSTROUTING -p tcp -d 10.20.201.1 --dport $ws_port -j MASQUERADE
    
    echo "  ✓ Gateway:$external_port → Server1:$ws_port (VNC:$vnc_port)"
done

# Server 2 (10.20.201.2) - Puertos WebSocket 6000-6050
for vnc_port in {5900..5950}; do
    ws_port=$((6000 + vnc_port - 5900))
    external_port=$((8000 + vnc_port - 5900))
    
    sudo iptables -t nat -A PREROUTING -p tcp --dport $external_port -j DNAT --to-destination 10.20.201.2:$ws_port
    sudo iptables -t nat -A POSTROUTING -p tcp -d 10.20.201.2 --dport $ws_port -j MASQUERADE
    
    echo "  ✓ Gateway:$external_port → Server2:$ws_port (VNC:$vnc_port)"
done

# Server 3 (10.20.201.3) - Puertos WebSocket 6000-6050
for vnc_port in {5900..5950}; do
    ws_port=$((6000 + vnc_port - 5900))
    external_port=$((9000 + vnc_port - 5900))
    
    sudo iptables -t nat -A PREROUTING -p tcp --dport $external_port -j DNAT --to-destination 10.20.201.3:$ws_port
    sudo iptables -t nat -A POSTROUTING -p tcp -d 10.20.201.3 --dport $ws_port -j MASQUERADE
    
    echo "  ✓ Gateway:$external_port → Server3:$ws_port (VNC:$vnc_port)"
done

echo ""
echo "✅ Reglas iptables configuradas!"
echo ""
echo "📝 Mapeo de puertos:"
echo "  Server 1 (10.20.201.1): Gateway puertos 7000-7050 → WebSocket 6000-6050"
echo "  Server 2 (10.20.201.2): Gateway puertos 8000-8050 → WebSocket 6000-6050"
echo "  Server 3 (10.20.201.3): Gateway puertos 9000-9050 → WebSocket 6000-6050"
echo ""
echo "💾 Guardar reglas permanentemente:"
echo "  sudo apt install iptables-persistent"
echo "  sudo netfilter-persistent save"
echo ""
echo "🔍 Ver reglas actuales:"
echo "  sudo iptables -t nat -L PREROUTING -n -v | grep DNAT"
echo "  sudo iptables -t nat -L POSTROUTING -n -v | grep MASQUERADE"
echo ""
echo "🗑️  Limpiar todas las reglas:"
echo "  sudo iptables -t nat -F PREROUTING"
echo "  sudo iptables -t nat -F POSTROUTING"
