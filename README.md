# proyecto_cloud

Proyecto web construido con FastAPI y SQLAlchemy para gestionar "templates" y despliegues.

Resumen rápido
- Framework: FastAPI (uvicorn)
- ORM: SQLAlchemy (+ pymysql)
- DB por defecto en `docker-compose.yml`: MySQL 8.0 (servicio `db`).

Contenido del repositorio
- `app/` - código de la aplicación (rutas, modelos, servicios, configuración)
- `db/init/` - scripts SQL para inicializar esquema y datos
- `docker-compose.yml` - define servicios `api`, `db` (MySQL) y `pma` (phpMyAdmin)

Quickstart (Docker)

1. Copia `.env.example` a `.env` y rellena los valores.

2. Levanta los servicios:

```powershell
docker compose up --build
```

3. Accede a la API en http://localhost:8000

Usar una base de datos MySQL externa

Configura la variable `DATABASE_URL` en `.env` con el formato:

```
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:3306/<database>
```

Si MySQL corre en tu Windows y usas Docker Desktop, desde el contenedor puedes usar `host.docker.internal` como `host`.

Archivos clave
- `app/main.py`: entrada de la app (routers y archivos estáticos).
- `app/db.py`: engine, SessionLocal y dependencia `get_db()`.
- `app/models.py`: modelos y relaciones.
- `app/routes/`: rutas web y API.

Lee `docs/ARCHITECTURE.md` para más detalles.
