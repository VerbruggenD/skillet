#!/usr/bin/env bash
set -euo pipefail

# Load .env if present to pick up DB credentials
if [ -f .env ]; then
  set -o allexport
  # shellcheck disable=SC1091
  . .env
  set +o allexport
fi

: "${POSTGRES_USER:=skillet}"
: "${POSTGRES_PASSWORD:=change-me}"
: "${POSTGRES_DB:=skillet}"
: "${POSTGRES_PORT:=5432}"

# Inside the compose network Postgres always listens on 5432; POSTGRES_PORT is only the host-side bind.
: "${DATABASE_URL:=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}}"

echo "Using DATABASE_URL=${DATABASE_URL}"

docker compose run --rm --entrypoint sh -e DATABASE_URL="${DATABASE_URL}" migrator -c "python -m pip install --upgrade pip setuptools wheel && python -m pip install alembic sqlalchemy psycopg[binary] && alembic -c migrations/alembic.ini upgrade head"
