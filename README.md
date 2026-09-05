# Skillet

Skillet is a self-hosted recipe manager for a shared household: add, browse and
search recipes through a React (Next.js) web app backed by a FastAPI REST
service and PostgreSQL. It runs as a small Docker Compose stack and is meant to
be placed behind your own reverse proxy (Caddy, nginx, Traefik, …) for TLS and
routing.

See also:
- [docs/design.md](docs/design.md) — architecture and feature plans
- [docs/api-design.md](docs/api-design.md) — API surface and authorization
- [docs/frontend-design.md](docs/frontend-design.md) — frontend design

## Features

- Browse and full-text search recipes (Postgres `tsvector` + GIN indexes)
- Rich browser-based recipe editor: structured ingredients and steps, tags
- Tag and favorites filtering, recipe detail pages
- Read-only recipes (`is_locked`) and role-based access: anonymous / user / admin
- Cookie-based login via server-side tokens (no JWT), first registered user becomes admin
- Suggestions: propose edits to recipes you don't own
- JSON export of recipes
- One-line health check (`/healthz`)

Not yet implemented (see the design docs): image upload, cook mode, serving-size
scaling, shopping lists, import-from-URL.

## Architecture

Single-origin, three containers plus a one-off migration container:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `api` | built from `backend/` | 8000 | FastAPI REST API, auth, health |
| `web` | built from `frontend/` | 3000 | Next.js frontend (opt-in via `--profile web`) |
| `postgres` | `postgres:16` | 5432 | database |
| `migrator` | `python:3.13-slim` | — | one-off container running Alembic migrations |

Data persists on host-bound volumes: `./data/postgres` (database) and
`./data/uploads` (recipe images, unused until image upload ships).

Auth is **same-origin only**: the frontend and API must share one hostname. Your
reverse proxy routes `/api/*` (and `/healthz`) to the API and everything else to
the frontend. Do **not** split the frontend and API onto different subdomains —
the httpOnly cookie would not be sent cross-site.

```
        skillet.example.com (TLS)
        ┌──────────────────────────────┐
        │        reverse proxy          │  e.g. Caddy / nginx
        │  /api/*  ──▶ api:8000         │
        │  /*      ──▶ web:3000         │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼────────────────┐
        │     docker compose stack       │
        │  api ──▶ postgres:16           │  data in ./data/*
        │  web                          │
        └────────────────────────────────┘
```

## Self-hosting quickstart

Requires Docker with compose v2.

1. **Clone and configure**

   ```bash
   git clone <your-repo-url> skillet
   cd skillet
   cp .env.example .env
   ```

   Edit `.env`:
   - `POSTGRES_PASSWORD` — a strong random password
   - `NEXT_PUBLIC_API_URL` — the **public site origin** clients will use, e.g.
     `https://skillet.example.com` (its `/api` path is proxied to the API)
   - `CORS_ORIGINS` — same origin, e.g. `https://skillet.example.com`
   - `COOKIE_SECURE=true` once you terminate TLS at your proxy

2. **Start the database and API**

   ```bash
   docker compose up -d
   ```

3. **Run migrations** (idempotent; safe to re-run)

   ```bash
   ./backend/run_migrations.sh
   ```

   This starts the one-off `migrator` container inside the compose network and
   applies every migration up to head. Alternatively, run Alembic yourself with
   `DATABASE_URL=postgresql+psycopg://skillet:<password>@localhost:5432/skillet`
   (`backend/README-migrations.md` has details).

4. **Build and start the frontend**

   ```bash
   docker compose --profile web up -d --build
   ```

5. **Verify**

   ```bash
   curl http://localhost:8000/healthz        # {"status":"ok"}
   docker compose ps
   ```

6. **Point your reverse proxy at it.** Example Caddyfile:

   ```
   skillet.example.com {
       @api path /api/* /healthz
       handle @api {
           reverse_proxy 127.0.0.1:8000
       }
       handle {
           reverse_proxy 127.0.0.1:3000
       }
   }
   ```

   nginx equivalent (note `/api` is passed through unrewritten, since route paths
   already include it):

   ```
   server {
       server_name skillet.example.com;
       listen 443 ssl;            # your cert management here
       location /api/  { proxy_pass http://127.0.0.1:8000; }
       location /healthz { proxy_pass http://127.0.0.1:8000; }
       location /      { proxy_pass http://127.0.0.1:3000; }
   }
   ```

   After enabling TLS, set `COOKIE_SECURE=true` in `.env` and
   `docker compose up -d` the API again.

7. **First run** — register the first account; it becomes the instance admin.
   Registration can be switched off later via the admin instance settings.

## Configuration reference

All values live in `.env` (see `.env.example`).

| Variable | Default | Used by | Notes |
|---|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `skillet` / `change-me` | postgres, api, migrator | DB credentials; set a strong password |
| `POSTGRES_PORT` | `5432` | compose | host-side bind only |
| `APP_PORT` | `8000` | compose | API host bind |
| `WEB_PORT` | `3000` | compose | frontend host bind (`--profile web`) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | build-time only | inlined into the frontend bundle; must be the public API origin |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | api | comma-separated browser origins |
| `COOKIE_SECURE` | `false` | api | set `true` behind HTTPS |
| `COOKIE_NAME` | `skillet-session` | api | session cookie name |
| `LOGIN_RATE_LIMIT` | `5/minute` | api | slowapi rule on the login endpoint |
| `UPLOAD_DIR` | `./uploads` | api | image upload directory (container path) |
| `MAX_UPLOAD_SIZE` | `5242880` (5 MiB) | api | max image upload size in bytes |
| `DATABASE_URL` | constructed by compose | api, migrator | optional explicit override |
| `SECRET_KEY` | `change-me` | api | reserved; not consumed yet |

## Backup

The Postgres container is the stock official image, so standard tooling applies:

```bash
docker compose exec postgres pg_dump -U skillet skillet > skillet-$(date +%F).sql
```

Restore:

```bash
docker compose exec -T postgres psql -U skillet skillet < skillet-YYYY-MM-DD.sql
```

Uploaded images (when shipped) live in `./data/uploads`. Back up or copy
`./data/` alongside your `pg_dump` output.

## Development

Non-Docker quickstart with the API pointing at the compose Postgres:

```bash
docker compose up -d postgres         # just the database

cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+asyncpg://skillet:change-me@localhost:5432/skillet
alembic -c migrations/alembic.ini upgrade head
uvicorn app.main:app --reload         # API on :8000

cd ../frontend
npm install
npm run dev                           # frontend on :3000
```

Tests and checks:

```bash
cd backend && .venv/bin/python -m pytest tests/ -q       # unit tests; add SKILLET_TEST_DATABASE_URL for integration tests
cd frontend && npm run lint && npm run typecheck && npm test -- --run
```

## CI / branching

CI (`ci.yml`, `migrations.yml`) runs lint, type checks, tests, and migrations on
PRs. Branching follows the model in [docs/design.md](docs/design.md)
(`main`, `develop`, `feature/*`).

## License

This project is released under the terms in the repository `LICENSE` file.