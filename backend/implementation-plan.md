# Skillet backend implementation plan

This document records the current implementation status and the next branch-by-branch work plan for the API design in `docs/api-design.md`.

## Current state

The repository contains the project skeleton and a first backend auth scaffold, including:

- async SQLAlchemy database setup
- FastAPI Users base wiring
- initial domain models for users, recipes, tags, and related tables
- placeholder routers for auth, recipes, tags, and images
- CI checks for linting, docstrings, type checking, and smoke-route tests

The backend is not yet complete against the API design specification. The current code is intentionally scaffold-only and should be treated as a starting point for the next implementation slice.

## Planned branch layout

### Branch 1: `feature/api-auth-users`

Complete the auth and user layer according to the design doc.

Goals:
- finalize the FastAPI Users model and access token model
- add custom registration route with `public_registration_enabled`
- set the first user as admin automatically
- add user routes and permissions
- add admin-only user listing/editing flows
- ensure `default_recipe_locked` works as a per-user preference

Files likely to change:
- `backend/app/core/users.py`
- `backend/app/models.py`
- `backend/app/routers/auth.py`
- `backend/app/core/deps.py` (to be created if needed)
- `backend/app/schemas/users.py` (to be created)

### Branch 2: `feature/api-settings`

Implement admin settings and route enforcement.

Goals:
- create `settings` table and default value for `public_registration_enabled`
- add `GET/PATCH /api/settings`
- make registration depend on instance setting
- add settings access checks for admin-only actions

Files likely to change:
- `backend/app/models.py`
- `backend/app/routers/settings.py` (to be created)
- `backend/app/core/config.py` or settings logic
- `backend/app/main.py`

### Branch 3: `feature/api-recipes`

Implement the core recipe lifecycle and lock behavior.

Goals:
- recipe create/list/get/update/delete
- per-user default lock behavior when creating recipes
- owner/admin authorization rules
- `is_locked` toggling logic
- optional recipe image attachment flow

Files likely to change:
- `backend/app/models.py`
- `backend/app/routers/recipes.py`
- `backend/app/schemas/recipes.py` (to be created)
- `backend/app/core/deps.py`

### Branch 4: `feature/api-suggestions-favorites`

Implement suggestions and favorites as first-class API features.

Goals:
- `recipe_suggestions` CRUD and review flow
- accept/reject suggestion actions
- favorite add/remove and list endpoint
- user ownership validation and admin override paths

Files likely to change:
- `backend/app/models.py`
- `backend/app/routers/recipes.py`
- `backend/app/routers/favorites.py` (to be created)
- `backend/app/routers/suggestions.py` (to be created)

### Branch 5: `feature/api-search-export`

Implement browsing/search/export features.

Goals:
- search by query and tag across recipe list endpoint
- full-text search index support
- export route for own recipes or admin-wide export
- tag create/get-or-create behavior in recipe writes

Files likely to change:
- `backend/app/routers/recipes.py`
- `backend/app/routers/tags.py`
- `backend/app/models.py`
- migrations and search setup

## Working rules

- Do not commit by default while implementing a feature slice.
- Keep each slice in a dedicated branch.
- Validate with the relevant subset of tests and lint/type checks after each branch.
- Use [docs/api-design.md](docs/api-design.md) as the source of truth for behavior.
- Keep placeholders and TODOs explicit until a feature is fully implemented.

## Next action

The next implementation branch should start with the auth/user layer and be treated as the first real feature implementation, not just scaffold work.
