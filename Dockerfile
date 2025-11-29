FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

# Instalar dependencias del sistema (SSH client, sshpass y websockify)
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    websockify \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
