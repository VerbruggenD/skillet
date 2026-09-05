# Skillet — High-Level Design

## Overview

**Skillet** is a self-hosted recipe manager: add, browse, and search recipes
through a React web app backed by a FastAPI REST service and PostgreSQL.
Beyond basic CRUD, Skillet is built around three user-facing pillars — a rich
in-browser recipe editor, a distraction-free step-by-step cook mode, and a
polished browsing experience — plus a shared-household model with anonymous
read access, per-recipe suggestions, and favorites. Designed to run as a small
set of containers behind an existing reverse proxy, with clean volume-based
persistence for easy backup.

Detailed specs live in companion docs:
- **`docs/api-design.md`** — backend API surface, endpoints, and authorization matrix (implemented)
- **`docs/frontend-design.md`** — frontend page inventory and component plan

This document covers only the overall architecture and feature set.

## Architecture

Two containers, managed via `docker-compose`:

- **`app`** — Python FastAPI backend serving a REST API, plus the built React
  frontend as static files. Handles authentication and access control.
  Exposes a single plain HTTP port; TLS and routing are left to the
  operator's own reverse proxy (Caddy, nginx, Traefik, etc.) — the app itself
  has no proxy or TLS logic baked in, so it stays portable across different
  hosting setups.
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
| No reverse proxy in the container | Keeps the stack portable — operators plug it into whatever proxy/TLS setup they already run. |
| PostgreSQL instead of SQLite | Enables proper concurrent multi-user access, and lets standard tools (pgBackRest, `pg_dump`, streaming replication) handle backup without custom scripting. |
| Postgres as its own container | Keeps the database's lifecycle and volume independent from the app, which is what backup tools expect and makes upgrades/restores simpler. |
| Two bind-mounted volumes | `./data/postgres` (DB) and `./data/uploads` (recipe images) live outside the containers, so rebuilding or upgrading the app never risks user data. |
| Fully async backend, FastAPI Users for auth | Async SQLAlchemy (`asyncpg`) throughout; FastAPI Users handles registration, login, password hashing, and access tokens via a cookie-based Database strategy (not JWT). |
| Three access tiers, one boolean | **Anonymous / user / admin**, represented by a single `is_superuser` flag rather than a free-text role column — anonymous read-access made a separate `viewer` role unnecessary. |
| Ingredients & steps as relational rows, not free text | Enables serving-size scaling, ingredient search, and shopping-list generation without re-parsing text later. |

## Access model

Shared-household cookbook, not per-user private boxes:

| Tier | What it is | Can do |
|---|---|---|
| **Anonymous** | No session/cookie | Browse and read non-locked recipes and tags only |
| **User** | Logged in | Everything anonymous can, plus: see all recipes (incl. locked), create recipes, fully edit/delete/lock recipes they own, favorite any recipe, suggest changes to recipes they don't own |
| **Admin** | Logged in, `is_superuser` | Everything a user can, plus edit/delete/lock any recipe regardless of owner, manage users, manage instance settings, resolve suggestions on any recipe |

**Recipe locking** — a per-recipe `is_locked` flag hides a recipe from
anonymous browsing while keeping it visible to any logged-in user; it's a
public/private toggle, not a broader permissions system. Each user has their
own `default_recipe_locked` preference applied at creation time, changeable
only by themselves (not overridable by admin) and never retroactive.

**Registration** is open by default but togglable instance-wide via an admin
setting; the first user to register automatically becomes admin.

## Data model

- **users** — id, email, hashed_password, is_active, is_superuser, is_verified, default_recipe_locked, created_at
- **access_tokens** — FastAPI Users' token table (cookie-based, server-side)
- **settings** — key/value store for instance-wide config (e.g. `public_registration_enabled`)
- **recipes** — id, owner_id, title, description, prep_time, cook_time, servings, source_url, is_locked, created_at
- **ingredients** — id, recipe_id, name, quantity, unit, notes
- **steps** — id, recipe_id, order, instruction
- **tags** — id, name
- **recipe_tags** — join table (many-to-many)
- **images** — filename reference stored in DB; actual file lives on the uploads volume
- **favorites** — user_id, recipe_id, created_at
- **recipe_suggestions** — id, recipe_id, suggested_by, payload (proposed field values), note, status (pending/accepted/rejected/withdrawn), created_at, resolved_at, resolved_by

## Feature breakdown

### Core
| Feature | Description |
|---|---|
| Recipe CRUD | Create, view, edit, and delete recipes with title, description, timing, servings, and instructions. |
| Structured ingredients | Ingredients stored as individual rows (name, quantity, unit) rather than free text, enabling scaling and search. |
| Step-by-step instructions | Instructions stored as ordered rows, editable and reorderable independently. |
| Image upload | Attach one or more photos per recipe, stored on a dedicated volume rather than in the database. |
| Tagging | Free-form tags with many-to-many association, created on the fly, used for filtering. |

### Recipe editor
| Feature | Description |
|---|---|
| Web-based recipe editor | Full recipe creation/editing happens in the browser. |
| Structured input forms | Dedicated inputs for ingredients and steps, with add/remove/reorder (drag-and-drop). |
| Live preview | Editor shows a preview of how the recipe will render in browse/cook views while editing. |
| Inline image upload | Drag-and-drop or file-picker image upload directly in the editor, with preview thumbnails before saving. |
| Autosave / draft state | Periodic autosave (or explicit "save draft") so in-progress edits aren't lost. |

### Cook mode
| Feature | Description |
|---|---|
| Step-by-step guided view | A focused, full-screen view that walks through one instruction step at a time. |
| Large, distraction-free UI | Big text, minimal chrome, readable from across a kitchen counter. |
| Ingredient checklist alongside steps | Relevant ingredients stay visible/checkable while cooking. |
| Step navigation | Next/previous controls (tap, swipe, or keyboard). |
| Built-in timers | Steps with a duration can trigger an inline timer with an alert on completion. |
| Servings-aware quantities | Quantities shown during cooking respect the serving size scaling chosen before starting. |
| Screen-wake support | Wake Lock API keeps the display active while cook mode is open. |

### Browsing experience
| Feature | Description |
|---|---|
| Recipe grid/list view | Visual, image-forward browsing with a toggle between grid and list layouts. |
| Sorting | Sort by name, date added, prep time, or last cooked. |
| Filter combinations | Combine tag filters, search text, and simple attribute filters (e.g. max prep time). |
| Recipe detail page | Clean, readable single-recipe view separate from cook mode. |
| Responsive design | Browsing and cook mode both work well on mobile/tablet. |

### Search & usability
| Feature | Description |
|---|---|
| Full-text search | Postgres `tsvector`/GIN index over titles, ingredients, and instructions. |
| Tag filtering | Browse or narrow recipes by one or more tags. |
| Serving size scaling | Ingredient quantities recalculated client-side based on a user-adjustable servings count; one shared implementation used by both browsing and cook mode. |
| Shopping list generation | Select multiple recipes and merge their ingredients into a single deduplicated, unit-aware list. |

### Accounts & access control
| Feature | Description |
|---|---|
| Authentication | Email/password login via FastAPI Users, httpOnly cookie-based access tokens. |
| Roles | Anonymous / user / admin via `is_superuser` (see Access model above). |
| Recipe ownership | Recipes tied to an `owner_id`; shared-household cookbook — all logged-in users see all recipes, ownership governs edit/delete rights. |
| Suggestions | Non-owners propose a full replacement of a recipe's editable fields instead of editing directly; owner or admin accepts or rejects. |
| Favorites | Any logged-in user can favorite/unfavorite any recipe. |
| Instance settings | Admin-configurable instance-wide options (e.g. open/closed registration). |

### Import & export
| Feature | Description |
|---|---|
| Recipe import from URL | Parse `schema.org/Recipe` JSON-LD metadata embedded on most recipe sites to pre-fill a new recipe. |
| Export / backup | Endpoint to export recipes (and metadata) as JSON, independent of the Postgres-level backup, for portability. |

### Operations
| Feature | Description |
|---|---|
| Bind-mounted persistence | Database and image data live on host-mounted volumes, decoupled from container lifecycle. |
| Postgres-native backups | Standard Postgres backup tooling works unmodified since Postgres runs as an unmodified official image. |
| Reverse-proxy agnostic | The app exposes a single HTTP port with no TLS or routing logic. |

## CI/CD & branching strategy

A lightweight variant of git-flow, sized for a small (possibly solo) project:

| Branch | Purpose | Protected |
|---|---|---|
| `main` | Always reflects the latest **released** state; every commit corresponds to a tagged release | Yes |
| `develop` | Integration branch; feature branches merge here first | Yes |
| `feature/*` | One branch per feature or fix, cut from `develop`; short-lived | No |
| `release/*` | Cut from `develop` when preparing a release; merges into both `main` and back into `develop` | No |
| `hotfix/*` | Cut from `main` for urgent fixes; merges into both `main` and `develop` | No |

Copilot code review runs automatically on PRs. CI (`ci.yml`) lints/type-checks/tests on every PR and builds a `:dev` image on pushes to `develop`; tagging `main` with `vX.Y.Z` triggers `release.yml`, which builds and pushes the versioned + `:latest` image to `ghcr.io`.
