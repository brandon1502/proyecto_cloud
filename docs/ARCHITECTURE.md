# Arquitectura de proyecto - proyecto_cloud

Este documento explica la arquitectura general de la aplicación, los componentes principales y cómo se relacionan.

Visión general
- Aplicación web basada en FastAPI.
- Acceso a datos mediante SQLAlchemy usando MySQL (driver: pymysql).
- Plantillas HTML con Jinja2 y archivos estáticos en `app/static`.

Componentes principales

1) app/
- `app/main.py` - Instancia la app FastAPI, monta los archivos estáticos y registra routers.
- `app/settings.py` - Configuración (lee variables desde `.env` mediante pydantic-settings).
- `app/db.py` - Inicializa el engine de SQLAlchemy, `SessionLocal` y la dependencia `get_db()`.
- `app/models.py` - Modelos de la base de datos: usuarios, roles, templates, flavours, template_vms, edges, slices, etc.
- `app/routes/` - Rutas agrupadas en módulos: `auth.py` (registro/login), `pages.py` (rutas que devuelven HTML), `templates.py` (API para crear/leer/exportar templates), `slices_api.py`, `flavours.py`, `deployments.py`.
- `app/services/` - Lógica de negocio reutilizable (ej. `users.py` para crear/autenticar usuarios y emitir tokens).

2) db/init/
- Scripts SQL de inicialización (00_schema.sql, 01_seed.sql) que usa el contenedor MySQL al arrancar para crear esquema y datos iniciales.

3) docker-compose.yml
- Define tres servicios principales: `api` (la app), `db` (MySQL) y `pma` (phpMyAdmin).
- Por defecto el contenedor `db` mapea `3306` interno a `3307` en el host.

Flujo de autenticación (resumen)
1. El usuario se registra vía `/auth/register` (formulario). `app.services.users.create_user` crea la fila en la tabla `users`.
2. El login (`/auth/login`) valida las credenciales, emite un JWT con `app.security.make_jwt` y guarda un hash en `api_tokens`.
3. El JWT se envía al cliente como cookie HTTP-only; `app.deps` contiene dependencias para leer/validar token y obtener el usuario actual.

Conectar una base de datos externa
- La aplicación lee `DATABASE_URL` desde `app/settings.py` (pydantic-settings lee `.env`).
- Formato esperado por SQLAlchemy con pymysql:

```
mysql+pymysql://user:password@host:3306/database
```

- Si ejecutas MySQL en la máquina host y usas Docker Desktop en Windows, desde el contenedor puedes usar `host.docker.internal` como `host`.
- Si usas la base de datos en otra máquina, usa la IP/DNS pública/privada y habilita acceso remoto en MySQL (bind-address y reglas de firewall).

Notas de mantenimiento
- Los modelos y relaciones están en `app/models.py`. Cambios en columnas o constraints requieren migraciones o aplicar los scripts SQL en `db/init`.
- Para exportar/importar datos puedes usar `mysqldump` y `mysql` client.

Dónde seguir
- Lee `README.md` (raíz) para comandos rápidos de inicio.
- Revisa `app/routes/templates.py` para entender la lógica que construye y guarda el JSON de templates.

Si quieres, puedo:
- Añadir diagramas (archivo `docs/diagram.png`) o diagramas en ASCII.
- Generar un script `scripts/import_dump.sh` para automatizar la importación de dumps.
