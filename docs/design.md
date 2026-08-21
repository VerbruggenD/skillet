# Skillet — High-Level Design

## Overview

**Skillet** is a self-hosted recipe manager: add, browse, and search your own
recipes through a React web app backed by a REST API and a PostgreSQL database.
Beyond basic CRUD, Skillet is built around three user-facing pillars — a rich
in-browser recipe editor, a distraction-free step-by-step cook mode, and a
polished browsing experience — backed by proper auth/roles and a clean CI/CD
pipeline. Designed to run as a small set of containers behind an existing reverse
proxy, with clean volume-based persistence for easy backup.

## Architecture

Two containers, managed via `docker-compose`:

- **`app`** — Node/FastAPI backend serving a REST API, plus the built React
  frontend as static files. Handles authentication and access control. Exposes a
  single plain HTTP port; TLS and routing are left to the operator's own reverse
  proxy (Caddy, nginx, Traefik, etc.) — the app itself has no proxy or TLS logic
  baked in, so it stays portable across different hosting setups.
- **`postgres`** — official `postgres` image, used as-is so standard backup
  tooling (pgBackRest, `pg_dump`, WAL archiving) works without modification.

```
                 ┌─────────────────────┐
                 │  Your reverse proxy │  (TLS, routing — not part of this stack)
                 └──────────┬──────────┘
                             │
        ┌────────────────────────────────────────┐
        │            docker-compose stack          │
        │                                           │
        │   ┌───────────────┐   ┌────────────────┐  │
        │   │ app container │──▶│ postgres        │  │
        │   │ API + auth    │   │ container       │  │
        │   │ + React build │   │                 │  │
        │   └───────┬───────┘   └────────┬────────┘  │
        │           │                    │           │
        │   ┌───────▼───────┐   ┌────────▼────────┐  │
        │   │ uploads volume │   │ pg-data volume  │  │
        │   │ ./data/uploads │   │ ./data/postgres │  │
        │   └───────────────┘   └─────────────────┘  │
        └────────────────────────────────────────┘
```

### Key decisions

| Decision | Rationale |
|---|---|
| No reverse proxy in the container | Keeps the stack portable — operators plug it into whatever proxy/TLS setup they already run, instead of fighting a baked-in one. |
| PostgreSQL instead of SQLite | Enables proper concurrent multi-user access, and lets standard tools (pgBackRest, `pg_dump`, streaming replication) handle backup without custom scripting. |
| Postgres as its own container | Keeps the database's lifecycle and volume independent from the app, which is what backup tools expect and makes upgrades/restores simpler. |
| Two bind-mounted volumes | `./data/postgres` (DB) and `./data/uploads` (recipe images) live outside the containers, so rebuilding or upgrading the app never risks user data. |
| JWT/cookie-based auth with roles | Supports multiple household users with different permission levels without depending on an external SSO layer. |
| FastAPI Users for auth (for now) | Handles registration, login, password hashing, and password reset out of the box via a SQLAlchemy adapter, saving time on the fiddly parts. It's in maintenance-only mode (security fixes, no new features) while its maintainers build a successor toolkit — acceptable short-term given its stability, but plan to migrate once the new toolkit matures. Role-based access control is not built in and is added on top via a custom `role` field and route dependencies. |
| Ingredients & steps as relational rows, not free text | Enables serving-size scaling, ingredient search, and shopping-list generation without re-parsing text later. |

## Data model

- **users** — id, email, password_hash, role (`admin` / `user`), created_at
- **sessions** — id, user_id, token/hash, expires_at (or stateless JWT, depending on preference)
- **recipes** — id, owner_id, title, description, prep_time, cook_time, servings, source_url, created_at
- **ingredients** — id, recipe_id, name, quantity, unit, notes
- **steps** — id, recipe_id, order, instruction
- **tags** — id, name
- **recipe_tags** — join table (many-to-many)
- **images** — filename reference stored in DB; actual file lives on the uploads volume

## API surface (representative)

```
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/recipes            list, with ?q= and ?tag= filters
GET    /api/recipes/:id        full recipe with ingredients + steps
POST   /api/recipes            create
PUT    /api/recipes/:id        update
DELETE /api/recipes/:id
POST   /api/recipes/:id/image  upload photo

GET    /api/tags
```

## Feature breakdown

### Core

| Feature | Description |
|---|---|
| Recipe CRUD | Create, view, edit, and delete recipes with title, description, timing, servings, and instructions. |
| Structured ingredients | Ingredients stored as individual rows (name, quantity, unit) rather than free text, enabling scaling and search. |
| Step-by-step instructions | Instructions stored as ordered rows, editable and reorderable independently. |
| Image upload | Attach one or more photos per recipe, stored on a dedicated volume rather than in the database. |
| Tagging | Free-form tags (e.g. "vegetarian", "quick", "italian") with many-to-many association, used for filtering. |

### Recipe editor

| Feature | Description |
|---|---|
| Web-based recipe editor | Full recipe creation/editing happens in the browser — no separate admin tool or markdown file editing required. |
| Structured input forms | Dedicated inputs for ingredients (name, quantity, unit) and steps, with add/remove/reorder (drag-and-drop) rather than a single freeform textarea. |
| Live preview | Editor shows a preview of how the recipe will render in browse/cook views while editing. |
| Inline image upload | Drag-and-drop or file-picker image upload directly in the editor, with preview thumbnails before saving. |
| Autosave / draft state | Periodic autosave (or explicit "save draft") so in-progress edits aren't lost, especially useful for longer recipes. |
| Import-assisted editing | When importing from a URL, the parsed result opens directly in the editor for review/cleanup before saving. |

### Cook mode

| Feature | Description |
|---|---|
| Step-by-step guided view | A focused, full-screen view that walks through one instruction step at a time, distinct from the normal recipe detail page. |
| Large, distraction-free UI | Big text, minimal chrome, designed to be readable from across a kitchen counter rather than up close. |
| Ingredient checklist alongside steps | Relevant ingredients for the current step (or the full list) stay visible/checkable while cooking. |
| Step navigation | Simple next/previous controls (tap, swipe, or keyboard) to move through steps at the cook's own pace. |
| Built-in timers | Steps that involve a duration (e.g. "simmer for 10 minutes") can trigger an inline timer with an alert on completion. |
| Servings-aware quantities in cook mode | Quantities shown during cooking respect the serving size scaling chosen before starting. |
| Screen-wake support | Keep the display active while cook mode is open, so the screen doesn't lock mid-recipe (browser Wake Lock API). |

### Browsing experience

| Feature | Description |
|---|---|
| Recipe grid/list view | Visual, image-forward browsing of the recipe collection, with a toggle between grid and list layouts. |
| Sorting | Sort by name, date added, prep time, or last cooked. |
| Filter combinations | Combine tag filters, search text, and simple attribute filters (e.g. max prep time) at once. |
| Recipe detail page | Clean, readable single-recipe view separate from cook mode — for browsing/reading rather than active cooking. |
| Responsive design | Browsing and cook mode both work well on mobile/tablet, since a kitchen use case is often not a desktop. |

### Search & usability

| Feature | Description |
|---|---|
| Full-text search | Postgres `tsvector`/GIN index over titles, ingredients, and instructions for fast search. |
| Tag filtering | Browse or narrow recipes by one or more tags. |
| Serving size scaling | Ingredient quantities recalculated client-side based on a user-adjustable servings count. |
| Shopping list generation | Select multiple recipes and merge their ingredients into a single deduplicated, unit-aware list. |

### Accounts & access control

| Feature | Description |
|---|---|
| Authentication | Email/password login using hashed passwords and httpOnly session cookies or JWTs, implemented via **FastAPI Users** (SQLAlchemy adapter) for registration, login, password hashing, and password reset. |
| Roles | `admin` (manage users, edit/delete any recipe) and `user` (manage own recipes, view all); optional `viewer` role for read-only sharing. Not provided by FastAPI Users — added as a custom `role` column plus a `require_role()` route dependency. |
| Recipe ownership | Recipes tied to an `owner_id`, allowing per-user recipe boxes if desired, or shared-cookbook mode by relaxing edit permissions to any authenticated user. |

> **Note on auth library:** FastAPI Users is in maintenance-only mode — the maintainers are building a successor Python auth toolkit intended to eventually replace it. Use FastAPI Users for the initial build (stable, saves significant time on registration/login/password-reset plumbing); plan to migrate to the new toolkit once it matures.

### Import & export

| Feature | Description |
|---|---|
| Recipe import from URL | Parse `schema.org/Recipe` JSON-LD metadata embedded on most recipe sites to pre-fill a new recipe. |
| Export / backup | Endpoint to export all recipes (and metadata) as JSON, independent of the Postgres-level backup, for portability. |

### Operations

| Feature | Description |
|---|---|
| Bind-mounted persistence | Database and image data live on host-mounted volumes, decoupled from container lifecycle. |
| Postgres-native backups | Standard Postgres backup tooling (pgBackRest, `pg_dump`, WAL archiving) works unmodified since Postgres runs as an unmodified official image. |
| Reverse-proxy agnostic | The app exposes a single HTTP port with no TLS or routing logic, so it can sit behind any existing reverse proxy setup. |

## CI/CD & branching strategy

### Branch model

A lightweight variant of git-flow, sized for a small (possibly solo) project:

| Branch | Purpose | Protected |
|---|---|---|
| `main` | Always reflects the latest **released** state. Every commit on `main` corresponds to a tagged release. | Yes |
| `develop` | Integration branch. Feature branches merge here first; this is the "testing" branch. | Yes |
| `feature/*` | One branch per feature or fix, cut from `develop`. Short-lived, deleted after merge. | No |
| `release/*` | Cut from `develop` when preparing a release (version bump, changelog, final fixes only — no new features). Merges into both `main` and back into `develop`. | No |
| `hotfix/*` | Cut from `main` for urgent fixes that can't wait for the next release cycle. Merges into both `main` and `develop`. | No |

```
feature/add-search ──┐
feature/shopping-list ┼──▶ develop ──▶ release/1.2.0 ──▶ main ──(tag v1.2.0)──▶ CI builds & pushes image
feature/import-url ───┘        ▲                              │
                                └────────── merge back ────────┘
```

### Feature flow

1. Branch `feature/xyz` off `develop`.
2. Open a **draft PR early** (optional) so CI runs continuously; mark it ready for review when done.
3. GitHub Copilot code review runs automatically on the PR (see below), alongside any human reviewer.
4. CI runs lint, type checks, and tests on every push to the PR.
5. Once approved and checks pass, merge into `develop` (squash merge keeps history clean).
6. When `develop` is stable and feature-complete for a release, cut a `release/x.y.z` branch: bump version, update changelog, fix any last-mile bugs directly on this branch.
7. Merge `release/x.y.z` into `main`, tag it (`vX.Y.Z`), then merge it back into `develop` so the version bump and fixes aren't lost.

### Branch protection rules

- `main` and `develop`: require PR review (Copilot + at least one human approval if not solo), require status checks (lint/test/build) to pass, disallow direct pushes and force-pushes.
- Optionally require branches to be up to date before merging, to avoid integration surprises.

### Copilot code review

Enabled via GitHub's repository settings (Copilot as an automatic PR reviewer, or requested manually with `/review`). It flags obvious issues (unused code, missing error handling, style inconsistencies) before a human review, which is especially useful on a project without a large review bandwidth. Configure it under **Settings → Code review → Copilot** and add it as a required reviewer on `main`/`develop` if you want it to run on every PR automatically.

### CI/CD pipeline (GitHub Actions)

Three workflows, roughly:

| Trigger | Workflow | Action |
|---|---|---|
| Pull request (any branch) | `ci.yml` | Lint, type-check, run backend/frontend tests. No image build/push. |
| Push to `develop` | `ci.yml` (extended) | Same as above, plus build the container image and push it tagged `:dev` (or `:develop`) to the registry, for optional staging use. |
| Push to `main` (i.e. a release merge) or a `v*` tag | `release.yml` | Build the multi-stage Docker image, tag it with the semver version (`vX.Y.Z`) and `:latest`, push to GitHub Container Registry (`ghcr.io`). |

Example release trigger:

```yaml
on:
  push:
    tags:
      - 'v*'
```

Tagging `main` with `vX.Y.Z` (rather than triggering on every push to `main`) keeps the release pipeline explicit — a merge into `main` alone doesn't publish anything until it's tagged, giving a clear, deliberate release step.

Using `ghcr.io` (GitHub Container Registry) keeps the image co-located with the repo and its permissions, with no extra registry account to manage — `docker-compose.yml` then just references `ghcr.io/<you>/recipe-app:latest` or a pinned version tag.

## Suggested build order

0. Set up repo structure and branching (`main`/`develop`), branch protection, and the CI workflow skeleton (lint/test on PR) before writing app code, so every subsequent step benefits from it
1. Postgres schema + migrations (users, recipes, ingredients, steps, tags)
2. Auth (register/login, password hashing, session/JWT middleware, role checks)
3. Recipe CRUD API + basic React browsing/detail views
4. Web-based recipe editor (structured forms, reordering, image upload, autosave)
5. Browsing experience polish (grid/list toggle, sorting, filter combinations, responsive layout)
6. Cook mode (step-by-step view, ingredient checklist, timers, wake lock)
7. Full-text search + tag filtering
8. Serving size scaling (frontend-only logic, shared by browsing and cook mode)
9. Shopping list generation
10. Recipe import from URL (feeding into the editor for review)
11. JSON export endpoint

## Getting started — TODO

A step-by-step checklist to actually start building. Each item lists what "done"
means for that step. The early items (0–3) are written to lock in the base
architecture, schema, and API surface up front — so that later feature work
(editor, cook mode, browsing, search, etc.) only adds new endpoints/components
rather than reshaping existing ones.

### 0. Repo & CI/CD scaffolding
- [ ] `main` and `develop` branches created, both protected (no direct pushes, require PR + passing checks)
- [ ] `ci.yml` workflow: runs lint + type-check + tests on every PR
- [ ] `release.yml` workflow: builds and pushes image to `ghcr.io` on `v*` tag
- [ ] Copilot enabled as an automatic PR reviewer
- [ ] `CONTRIBUTING.md` or README section documenting the branch flow (feature → develop → release → main)

### 1. Container & environment skeleton
- [ ] `docker-compose.yml` with `app` and `postgres` services, using env vars (not hardcoded secrets) for DB credentials and JWT secret
- [ ] `./data/postgres` and `./data/uploads` bind mounts wired up and confirmed to persist across `docker-compose down && up`
- [ ] `app` Dockerfile is multi-stage (React build → copy into final backend image), builds successfully in CI
- [ ] `.env.example` documents every required environment variable
- [ ] App container exposes exactly one HTTP port; confirmed reachable via a manually configured local reverse proxy (Caddy/nginx) as a smoke test

### 2. Database schema (full schema up front)
- [ ] Migration tool chosen and wired up (e.g. Alembic)
- [ ] Full schema created in one pass, covering **every** table the design anticipates — not just what's needed for CRUD: `users`, `recipes` (incl. `owner_id`), `ingredients`, `steps`, `tags`, `recipe_tags`, `images` — so later features (scaling, search, ownership) don't require schema migrations to *add* columns/tables, only to populate/use them
- [ ] `role` column on `users` included from the start, even before role-checking logic exists
- [ ] Postgres `tsvector`/GIN index columns added now (even if search isn't implemented yet), so full-text search is a query-layer feature later, not a schema change
- [ ] Migration runs cleanly against a fresh `postgres` container in CI

### 3. API surface (defined and stubbed up front)
- [ ] Full REST endpoint list from the design doc scaffolded (even if some just return `501 Not Implemented` initially) — auth, recipes CRUD, images, tags, search, export — so the frontend can be built against a stable, known contract from day one
- [ ] OpenAPI schema auto-generated (free with FastAPI) and reviewed for consistency (naming, status codes, pagination shape) before any frontend work starts
- [ ] Consistent error response shape decided and documented (e.g. `{ "detail": "..." }`) and used everywhere
- [ ] Pagination strategy decided for `GET /api/recipes` (e.g. limit/offset or cursor) and applied from the first implementation, since retrofitting pagination later changes the response shape

### 4. Auth & roles
- [ ] FastAPI Users integrated with the SQLAlchemy adapter against the `users` table from step 2
- [ ] Register/login/logout working end-to-end with httpOnly cookies
- [ ] Password hashing verified (not plaintext, not reversible)
- [ ] `require_role()` dependency implemented and applied to at least one admin-only route as a test case
- [ ] `GET /api/auth/me` returns the current user including role

### 5. Recipe CRUD + base frontend shell
- [ ] All recipe CRUD endpoints fully implemented (not stubbed) against the real schema
- [ ] React app skeleton: routing, API client (with auth cookie handling), and a global auth/user context
- [ ] Basic (unstyled is fine) list and detail views proving the full request path: browser → app container → Postgres → back
- [ ] Recipe ownership enforced (`owner_id` checked on update/delete) with a passing test for a non-owner being rejected

### 6. Recipe editor
- [ ] Structured forms for title/description/timing/servings
- [ ] Add/remove/reorder for ingredients and steps, persisted correctly via API on save
- [ ] Image upload wired to the `/data/uploads` volume, with the file reference stored on the `images` table
- [ ] Autosave or explicit draft save implemented and tested (refresh mid-edit doesn't lose data)
- [ ] Live preview reflects actual saved-state rendering, not a separate mock

### 7. Browsing experience
- [ ] Grid/list toggle, sorting (name/date/prep time), and tag+search filter combinations all working against real data
- [ ] Responsive layout verified on a mobile viewport, not just desktop
- [ ] Recipe detail page finalized as the "read" view, distinct from cook mode

### 8. Cook mode
- [ ] Step-by-step full-screen view with next/previous navigation
- [ ] Ingredient checklist visible/checkable alongside steps
- [ ] Timers implemented for steps with a duration, with a clear completion alert
- [ ] Wake Lock API integrated (with a graceful fallback for unsupported browsers)
- [ ] Confirmed cook mode respects the servings scaling chosen beforehand

### 9. Search & scaling
- [ ] Full-text search implemented against the `tsvector` columns from step 2
- [ ] Serving size scaling logic shared between browsing/detail and cook mode (one implementation, not duplicated)

### 10. Shopping list & import/export
- [ ] Shopping list generation merges/dedupes ingredients across selected recipes, with unit-aware combination
- [ ] URL import parses `schema.org/Recipe` JSON-LD and opens the result in the editor (step 6) for review before saving
- [ ] JSON export endpoint returns a complete, re-importable dump of a user's (or all) recipes

