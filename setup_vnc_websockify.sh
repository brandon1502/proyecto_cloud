#!/bin/bash
# Script para instalar websockify en los servers 1/2/3 (10.20.201.1/2/3)
# Ejecutar este script EN CADA SERVER (donde corren las VMs)

set -e

echo "🚀 Instalando websockify para acceso VNC automático..."

# 1. Instalar dependencias
echo "📦 Instalando websockify..."
sudo apt update
sudo apt install -y python3-websockify python3-numpy

# 2. Crear script wrapper para calcular puerto WebSocket
echo "⚙️ Creando script wrapper..."
sudo tee /usr/local/bin/websockify-vnc-proxy > /dev/null <<'EOF'
#!/bin/bash
# Wrapper para websockify que calcula el puerto WebSocket
# Argumento: puerto VNC (5900-5950)
VNC_PORT=$1

# Calcular puerto WebSocket: 6000 + (VNC_PORT - 5900)
# Ejemplo: VNC 5900 -> WS 6000, VNC 5950 -> WS 6050
WS_PORT=$((6000 + VNC_PORT - 5900))

echo "Iniciando websockify: WS puerto $WS_PORT -> VNC localhost:$VNC_PORT"
exec /usr/bin/websockify $WS_PORT localhost:$VNC_PORT
EOF

sudo chmod +x /usr/local/bin/websockify-vnc-proxy

# 3. Crear servicio systemd para cada puerto VNC
echo "⚙️ Creando servicio systemd..."
sudo tee /etc/systemd/system/vnc-websockify@.service > /dev/null <<'EOF'
[Unit]
Description=VNC WebSocket Proxy for VNC port %i
After=network.target

[Service]
Type=simple
User=ubuntu
# Usa el wrapper que calcula el puerto WebSocket automáticamente
ExecStart=/usr/local/bin/websockify-vnc-proxy %i
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Recargando systemd..."
sudo systemctl daemon-reload

# 4. Habilitar e iniciar servicios para puertos VNC 5900-5950
echo "🎯 Iniciando servicios para puertos VNC 5900-5950..."
for port in {5900..5950}; do
    ws_port=$((6000 + port - 5900))
    echo "  Configurando VNC:$port -> WebSocket:$ws_port"
    sudo systemctl enable vnc-websockify@${port}.service 2>/dev/null || true
    sudo systemctl restart vnc-websockify@${port}.service
done

# 5. Verificar que algunos estén corriendo
echo ""
echo "✅ Verificando servicios..."
sleep 2

# Verificar algunos puertos
for port in 5900 5901 5902; do
    if sudo systemctl is-active --quiet vnc-websockify@${port}.service; then
        ws_port=$((6000 + port - 5900))
        echo "  ✓ VNC:$port -> WebSocket:$ws_port [ACTIVO]"
    else
        echo "  ✗ Puerto $port [ERROR]"
    fi
done

echo ""
echo "📊 Puertos WebSocket escuchando (rango 6000-6050):"
sudo netstat -tuln | grep -E ":(60[0-4][0-9]|605[0])" | head -5

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "📝 Configuración:"
echo "  - VNC puerto 5900 → WebSocket ws://SERVER_IP:6000"
echo "  - VNC puerto 5901 → WebSocket ws://SERVER_IP:6001"
echo "  - VNC puerto 5950 → WebSocket ws://SERVER_IP:6050"
echo ""
echo "🔍 Para verificar un servicio específico:"
echo "  sudo systemctl status vnc-websockify@5900"
echo ""
echo "📋 Para ver logs:"
echo "  sudo journalctl -u vnc-websockify@5900 -f"
echo ""
echo "🛑 Para detener todos los servicios:"
echo "  for port in {5900..5950}; do sudo systemctl stop vnc-websockify@\${port}; done"
