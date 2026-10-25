# SportyClub

SaaS **multitenant** para administrar clubes deportivos. Cada club vive en su
propio subdominio y sus datos quedan aislados a nivel de base de datos mediante
**Row-Level Security (RLS)** de PostgreSQL.

- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2 async + Alembic. API **REST**.
- **Base de datos**: PostgreSQL 16 con RLS por `tenant_id`.
- **Panel**: Next.js (App Router) + React + Tailwind, que consume la API a traves
  de un BFF (route handlers) con cookies httpOnly.
- **Auth**: JWT access + refresh con rotacion, RBAC por club.
- **Infra**: Docker Compose + Caddy (TLS + wildcard de subdominios).

## Arquitectura multitenant

- El **club (tenant)** se resuelve por el **subdominio** del Host
  (`club1.tudominio.com`). Tambien se acepta `X-Forwarded-Host` cuando hay un
  proxy delante (Caddy o el BFF del panel).
- Cada tabla de dominio tiene `tenant_id` y una politica RLS que compara con
  `current_setting('app.current_tenant')`. La app se conecta con el rol
  **`app_user`** (sin privilegios, sujeto a RLS); las migraciones usan el rol
  **owner** (superusuario).
- Cada peticion abre una transaccion y fija el tenant con `set_config(...)`.
- Sin contexto de tenant, RLS no devuelve ninguna fila (fail-closed).
- Tablas de plataforma (`tenants`, `platform_admins`, `permissions`) no tienen RLS.

Una cuenta pertenece a **un solo club** (`UNIQUE(tenant_id, email)`). El alta de
clubes es **solo por invitacion** desde un superadmin de plataforma.

## Estructura

```
sportyclub/
├── docker-compose.yml      # postgres + caddy + backend + admin
├── Caddyfile               # wildcard de subdominios + TLS
├── .env.example
├── backend/
│   ├── app/
│   │   ├── core/           # config, db, security, deps, paginacion, email
│   │   ├── tenancy/        # resolucion de subdominio, contexto, RLS
│   │   ├── modules/        # clubs, platform, auth, users, rbac, invitations, audit
│   │   └── api/v1/router.py
│   ├── alembic/versions/   # migracion inicial + politicas RLS
│   ├── scripts/            # start.sh, seed.py
│   └── tests/              # aislamiento, auth, rbac, plataforma
└── admin/                  # Next.js (login, invitaciones, usuarios, roles)
```

## Puesta en marcha (desarrollo)

### 1. Variables de entorno

```bash
cp .env.example .env
# Ajusta como minimo SECRET_KEY (openssl rand -hex 32) y las contrasenas.
```

### 2. PostgreSQL

```bash
docker compose up -d postgres
```

### 3. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head          # crea tablas, rol app_user y politicas RLS
python -m scripts.seed        # catalogo de permisos + superadmin de plataforma

uvicorn app.main:app --reload # http://localhost:8000  (docs en /docs)
```

### 4. Panel

```bash
cd admin
npm install
npm run dev                   # http://localhost:3000
```

### 5. Primer uso

El subdominio identifica al club. En local usamos `lvh.me` (resuelve a 127.0.0.1):

1. Entra al **panel de plataforma** en `http://lvh.me:3000/platform/login` con
   `PLATFORM_ADMIN_EMAIL` / `PLATFORM_ADMIN_PASSWORD`.
2. Crea un club (nombre, subdominio y correo del dueno). El panel te muestra el
   **enlace de invitacion** para copiar (el correo tambien se imprime en el log
   del backend).
3. Abre el enlace en el subdominio del club
   (`http://tu-club.lvh.me:3000/accept-invitation?token=...`), crea la cuenta del
   dueno y administra el club desde `/dashboard`.

> Nota: el panel de plataforma vive en el **dominio raiz** (apex); el panel del
> club, en el **subdominio** de cada club.

## API (v1)

- **Plataforma** (`/api/v1/platform/...`): `auth/login|refresh|logout|me`,
  `clubs`, `admins`.
- **Club** (`/api/v1/...`, resuelto por subdominio): `auth/*`, `users`, `roles`,
  `invitations`, `audit-logs`, `disciplines`, `metrics` y `people` (con
  `guardians`, `dependents`, `profile` y `measurements`).

### Roles del club

| Rol | Permisos |
|---|---|
| `owner` (dueno) | Todo. Lo recibe quien acepta la invitacion al crear el club; siempre queda al menos uno activo. |
| `admin` | Todo salvo `club:update` y la gestion de roles. No puede nombrar duenos. |
| `coach` (entrenador) | Ver deportistas y acudientes, editar la ficha tecnica y registrar mediciones. |
| `staff` | Solo lectura. |
| `member` | `club:read`. |

Al arrancar, la API sincroniza los roles del sistema de todos los clubes con el
catalogo (`app/modules/rbac/catalog.py`): crea los que falten y anade permisos
nuevos, sin quitar nunca ninguno.

Documentacion interactiva: `http://localhost:8000/docs`.

## Tests

Los tests usan una base de datos real (validan RLS). Apunta a tu PostgreSQL:

```bash
cd backend
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export POSTGRES_USER=sportyclub POSTGRES_PASSWORD=sportyclub POSTGRES_DB=sportyclub_test
pytest -q
```

Cubren: aislamiento entre dos clubes (RLS), login/refresh/rotacion, RBAC y
operaciones de plataforma.

## Calidad de codigo

```bash
cd backend && ruff check app tests scripts && mypy app
```

## Produccion

- `docker compose up -d --build` levanta Postgres, la API, el panel y Caddy.
- Caddy gestiona TLS y el wildcard de subdominios (ver `Caddyfile`; el
  certificado wildcard requiere el reto DNS de tu proveedor).
- Cambia todas las credenciales de `.env` y define `BASE_DOMAIN` con tu dominio.

## Roadmap

- **Fase 1** ✅: fundacion multitenant (RLS, auth, RBAC, invitaciones, auditoria).
- **Fase 2** ✅: panel de plataforma (clubes y administradores).
- **Fase 3**: modulos de dominio.
  - **3A** ✅: personas (deportistas y acudientes), ficha tecnica con historial
    de mediciones, disciplinas y roles dueno/entrenador.
  - **3B**: planes y membresias (con responsable de pago).
  - **3C**: mensualidades (vencimiento el dia 5, recargo por mora configurable)
    y registro de pagos.
  - Despues: equipos/categorias, entrenamientos/sesiones, reservas y comunicacion.
- **Fase 4**: observabilidad, backups, colas y notificaciones reales.
