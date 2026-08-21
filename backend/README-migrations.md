Alembic migrations

How to run migrations locally:

1. Ensure a Postgres URL is available via `DATABASE_URL` or in `.env`.

2. From the repo root, run (example using the compose Postgres):

```bash
# start Postgres
docker compose up -d postgres

# set DATABASE_URL to point to the running container; example:
export DATABASE_URL=postgresql://skillet:change-me@localhost:5432/skillet

# run alembic (installed in your Python env)
alembic -c backend/migrations/alembic.ini upgrade head
```

Notes:
- `backend/migrations/env.py` reads `DATABASE_URL` from the environment.
- The initial migration creates `users`, `sessions`, `recipes`, `ingredients`, `steps`, `tags`, `recipe_tags`, and `images`, and a GIN index on `recipes.search_vector`.
