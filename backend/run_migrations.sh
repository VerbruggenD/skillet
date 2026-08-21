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

: "${DATABASE_URL:=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:${POSTGRES_PORT}/${POSTGRES_DB}}"

echo "Using DATABASE_URL=${DATABASE_URL}"

docker compose run --rm migrator sh -c "python -m pip install --upgrade pip setuptools wheel && python -m pip install alembic sqlalchemy psycopg[binary] && alembic -c migrations/alembic.ini upgrade head"
