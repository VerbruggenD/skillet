# Skillet

Skillet is a self-hosted recipe manager: add, browse and search recipes via a
React web app backed by a FastAPI REST service and PostgreSQL. The project is
designed to run as a small set of containers (app + postgres) and to be placed
behind an operator-managed reverse proxy for TLS and routing.

See the full design notes in [docs/design.md](docs/design.md).

## Key features

- Rich browser-based recipe editor (structured ingredients & steps)
- Distraction-free cook mode with step-by-step guidance and timers
- Image upload and bind-mounted uploads volume for persistent media
- Full-text search (Postgres `tsvector` + GIN indexes planned)
- Role-based auth (admin / user) and per-recipe ownership

## Architecture

Two-container stack (managed with `docker-compose`):

- `app` — Python FastAPI backend (serves REST API and the built frontend)
- `postgres` — official Postgres image, data persisted to `./data/postgres`

The app exposes a single HTTP port and expects TLS/routing to be handled by
your reverse proxy (Caddy, nginx, Traefik, etc.). See the design doc for
details: [docs/design.md](docs/design.md).

## Tech stack

- Backend: Python 3.13, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic
- Frontend: Next.js / React (see `frontend/`)
- DB: PostgreSQL (official image)
- CI: GitHub Actions (lint/test on PRs, release builds on tags)

## Quickstart (Docker)

Build and run the development stack with docker-compose from the repository
root. This provides a quick way to start the app and Postgres locally.

```bash
docker compose build
docker compose up -d
# check logs:
docker compose logs -f app
```

By default the `app` container listens on port `8000`. The compose file is set
up for bind-mounted volumes for the Postgres data and uploads so user data
persists across restarts.

To build just the backend image:

```bash
docker build -t skillet-backend ./backend
docker run --rm -p 8000:8000 skillet-backend
```

The backend Dockerfile is at [backend/Dockerfile](backend/Dockerfile#L1-L50).

## Development notes

- Backend: Python 3.13+. Use a virtual environment in `backend/` and install
	dependencies from `pyproject.toml` (or reproduce the environment that CI
	uses). The backend app entrypoint is `app.main:app` and runs under Uvicorn.
- Frontend: see `frontend/` for the Next.js app. Typical commands:

```bash
cd frontend
npm install
npm run dev
```

## CI / Branching

Follow the project's branching model described in [docs/design.md](docs/design.md)
(`main`, `develop`, `feature/*`, `release/*`). CI runs lint/type/tests on PRs
and builds/publishes images for release tags.

## Contributing

- Open a feature branch off `develop` and open a PR. Keep changes small and
	focused. Protect `main` and `develop` with branch protection rules and
	require passing checks before merge.

## License

This project is released under the terms in the repository `LICENSE` file.

