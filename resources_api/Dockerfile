FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . /app/resources_api/

# Exponer puerto
EXPOSE 8001

# Comando por defecto
CMD ["uvicorn", "resources_api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
