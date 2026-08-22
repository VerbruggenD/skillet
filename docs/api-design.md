# Skillet Backend API — Design & Build Plan (async, FastAPI Users, 3-tier access)

Everything below assumes: fully async FastAPI Users auth, and three access
tiers — **anonymous**, **user**, **admin** — with recipe *suggestions* and
*favorites* as new first-class concepts. Database design proceeds alongside the
API, endpoint by endpoint, rather than being fully locked up front — the schema
below is the current best guess and is expected to gain columns/tables as each
router gets built.

## 1. Access model

Three tiers, not three DB roles — this is simpler than it sounds:

| Tier | What it is | DB representation |
|---|---|---|
| **Anonymous** | No session/cookie at all | not a row — the absence of an authenticated user |
| **User** | Logged in, `is_superuser=False` | `users.is_superuser = false` |
| **Admin** | Logged in, `is_superuser=True` | `users.is_superuser = true` |

This is a deliberate simplification from the earlier draft: once anonymous
covers "read-only," you don't need a separate `viewer` DB role or a
free-text `role` column — a single boolean is enough. Drop the `role` string
column from the plan; `is_superuser` (which FastAPI Users already requires, see
§3) is the whole story.

**Permission summary**:
- **Anonymous**: browse and read non-locked recipes and tags. Nothing else —
  no favorites, no suggestions, no creating/editing anything.
- **User**: everything anonymous can do, plus: see *all* recipes including
  locked ones (this is a shared household cookbook, not per-user private
  boxes — that earlier open question is now settled), create recipes, fully
  edit/delete/lock recipes **they own**, favorite any recipe, and *suggest*
  changes to recipes they don't own (never edit or delete those directly).
- **Admin**: everything a user can do, plus full edit/delete/lock on *any*
  recipe regardless of owner, manage users, manage instance settings, and
  resolve (accept/reject) suggestions on any recipe (not just their own).

## 2. New concepts this introduces

### Recipe locking
A recipe gets an `is_locked` boolean. Locked = hidden from anonymous browsing,
still fully visible to any logged-in user. This is the *only* thing locking
controls — it's a public/private toggle, not a permissions system of its own.

**Default is unlocked**, but this is a **per-user preference**, not a fixed
constant: `users.default_recipe_locked` (boolean, default `false`) — whatever
a user's own setting is gets applied as `is_locked` when *they* create a new
recipe. Each user can flip their own default in `PATCH /api/users/me` (part of
the normal FastAPI Users update payload — just an extra field on the schema,
no new endpoint needed) without affecting anyone else's default or any
already-created recipe.

**Who can change what, precisely** — this has two independent layers, worth
spelling out since it's easy to conflate them:
- **The per-user default** (`users.default_recipe_locked`) — only the user
  themselves can change their own default. Admin does **not** override this;
  it's a personal preference, not an instance policy.
- **An individual recipe's `is_locked` flag** — the owner can change it
  (via `PATCH /api/recipes/{id}`) for their own recipes, and **admin can
  override it on any recipe** regardless of owner, same as admin's general
  edit/delete authority. Changing a recipe's lock state after creation never
  touches the owner's stored default — that default only applies at
  *creation* time for new recipes.

### Suggestions
A lightweight edit-proposal system, not a full diff/patch engine: a non-owner
submits a *complete proposed replacement* of the editable fields (title,
description, ingredients, steps, etc. — same shape as a recipe update payload),
plus an optional note. The owner or an admin reviews it and either **accepts**
(applies the proposed fields to the real recipe) or **rejects** it. No partial
merge logic, no field-by-field diffing — keep this simple for v1; a real
diff/merge UI is a much bigger feature and not something the API needs to solve
today.

**Confirmed**: an owner cannot submit a suggestion on their own recipe — they
edit directly instead. `POST /api/recipes/{id}/suggestions` returns 400 if the
caller is the recipe's own owner (403 would also be defensible, but 400 reads
more accurately here — it's not a permissions problem, it's a "this action
doesn't apply to you" problem, since the owner *is* allowed to change the
recipe, just via a different endpoint).

New table: `recipe_suggestions`
- `id`, `recipe_id` (FK), `suggested_by` (FK → users), `payload` (JSON — the
  proposed field values), `note` (text, optional), `status`
  (`pending`/`accepted`/`rejected`/`withdrawn`), `created_at`, `resolved_at`,
  `resolved_by` (FK → users, nullable)

### Favorites
Simple many-to-many, no extra fields needed beyond the join itself.

New table: `favorites`
- `user_id` (FK, PK part), `recipe_id` (FK, PK part), `created_at`

## 3. Async + FastAPI Users (unchanged from prior decision, summarized)

- **Everything is async**: `core/db.py` uses `create_async_engine`/
  `AsyncSession` (`asyncpg` driver), every router handler is `async def`.
  Alembic migrations stay sync — that's normal, migrations run offline from
  the request path.
- **User model changes**: `password_hash` → `hashed_password`, add
  `is_active`, `is_superuser`, `is_verified`, and `default_recipe_locked`
  (booleans — the last one is the per-user lock-default preference from §2).
  Drop the plan for a separate `role` column per §1.
- **Sessions → access tokens**: replace the hand-rolled `sessions` table with
  FastAPI Users' `AccessToken` model (Database strategy — opaque server-side
  tokens via cookie transport, not JWT).
- **Skip password reset / email verification routers for v1** — no SMTP, no
  untrusted public signup to protect against. Admin can reset a password
  directly via `PATCH /api/users/{id}`.
- **First user becomes admin** automatically (`UserManager.on_after_register`
  or an overridden `create()`, checking `count(User) == 0`) so there's a
  working admin account from first boot without a manual DB edit.
- **Registration policy**: open by default, but this is an **instance-wide
  admin setting** (`settings` table, key `public_registration_enabled`,
  default `true`), not a fixed constant — anyone running Skillet fully
  publicly needs to be able to close it. Because of this, **don't mount
  FastAPI Users' `get_register_router()` directly** — it has no hook for a
  runtime on/off switch. Instead, write a thin custom
  `POST /api/auth/register` route that: (1) checks
  `settings["public_registration_enabled"]`, returns 403 if disabled and the
  caller isn't an admin, then (2) calls `UserManager.create()` internally,
  same as the library route would have. This keeps the same request/response
  shape the library would've given you, just with the gate in front of it.

## 4. Full endpoint list

### Auth & users
```
POST   /api/auth/cookie/login       [FastAPI Users]
POST   /api/auth/cookie/logout      [FastAPI Users]
POST   /api/auth/register           [CUSTOM — gated by `public_registration_enabled` setting, see §3]
GET    /api/users/me                 [FastAPI Users]
PATCH  /api/users/me                 [FastAPI Users]
GET    /api/users/{id}                [FastAPI Users, admin only]
PATCH  /api/users/{id}                [FastAPI Users, admin only]
DELETE /api/users/{id}                [FastAPI Users, admin only]
GET    /api/users                      [CUSTOM — list, admin only]
POST   /api/users                      [CUSTOM — admin creates a user directly, invite-only mode]
```

### Settings (new — "admins manage some settings")
```
GET    /api/settings          admin only — instance-wide config
PATCH  /api/settings          admin only — update settings
```
New table: `settings` (`key` string PK, `value` text/JSON) — simple key/value
store, not a full config system. Unlike the earlier draft, this table can't be
deferred to a later migration: `public_registration_enabled` (default `true`)
is needed from the very first request to `/api/auth/register`, so `settings`
and its one real key ship in the *same* migration as the FastAPI Users setup
(§3), not a follow-up one. Add further keys only as a real need for them shows
up while building later routers.

### Recipes
```
GET    /api/recipes                anonymous: non-locked only; logged in: all
                                    ?q=, ?tag=, ?sort=, ?page=/?limit=
GET    /api/recipes/{id}           anonymous: 404 if locked; logged in: any
POST   /api/recipes                any logged-in user; owner_id = self
PATCH  /api/recipes/{id}           owner or admin only (incl. toggling is_locked)
DELETE /api/recipes/{id}           owner or admin only — non-owner user: 403
POST   /api/recipes/{id}/image     owner or admin only
DELETE /api/recipes/{id}/image/{image_id}   owner or admin only
```

### Suggestions (new)
```
POST   /api/recipes/{id}/suggestions             any logged-in user except
                                                  the recipe's own owner
GET    /api/recipes/{id}/suggestions             owner or admin (review queue
                                                  for that recipe)
GET    /api/suggestions/mine                     current user's own submitted
                                                  suggestions + their status
POST   /api/recipes/{id}/suggestions/{sid}/accept   owner or admin — applies
                                                     payload to the recipe
POST   /api/recipes/{id}/suggestions/{sid}/reject   owner or admin
DELETE /api/recipes/{id}/suggestions/{sid}          suggestion's own author
                                                     (only while pending), or admin
```

### Favorites (new)
```
GET    /api/favorites               current user's favorited recipes
POST   /api/recipes/{id}/favorite   any logged-in user
DELETE /api/recipes/{id}/favorite   any logged-in user
```

### Tags
```
GET    /api/tags              anonymous + logged in (used for browse filters)
DELETE /api/tags/{id}         admin only
```
Create tags on the fly (get-or-create by name) inside recipe create/update.

### Search & export
```
GET    /api/recipes?q=...     full-text search folded into the list endpoint
GET    /api/export             logged-in only; own recipes; admin: ?all=true
```

### Roadmap (not v1)
```
POST   /api/import/url         schema.org/Recipe JSON-LD → unsaved draft recipe
POST   /api/shopping-list      { recipe_ids } → merged ingredient list, stateless
```

### Health
```
GET    /healthz                 already implemented, no changes needed
```

## 5. Authorization matrix

| Endpoint | Anonymous | user (not owner) | owner | admin |
|---|---|---|---|---|
| `GET /api/recipes`, `/{id}` | ✅ non-locked only | ✅ all | ✅ | ✅ |
| `POST /api/recipes` | ❌ | ✅ | — | ✅ |
| `PATCH/DELETE /api/recipes/{id}` (incl. lock toggle) | ❌ | ❌ | ✅ | ✅ |
| `POST/DELETE .../image` | ❌ | ❌ | ✅ | ✅ |
| `POST /api/recipes/{id}/suggestions` | ❌ | ✅ | ❌ (400 — edit directly instead) | ✅ (subject to same 400 if admin owns it) |
| `GET .../suggestions` (review queue) | ❌ | ❌ | ✅ | ✅ |
| `.../suggestions/{sid}/accept`, `/reject` | ❌ | ❌ | ✅ | ✅ |
| `GET /api/suggestions/mine` | ❌ | ✅ (own) | — | ✅ |
| `GET /api/favorites`, `POST/DELETE .../favorite` | ❌ | ✅ | — | ✅ |
| `GET /api/tags` | ✅ | ✅ | — | ✅ |
| `DELETE /api/tags/{id}` | ❌ | ❌ | — | ✅ |
| `GET /api/users`, `POST /api/users`, `/{id}` ops | ❌ | ❌ | — | ✅ |
| `GET/PATCH /api/settings` | ❌ | ❌ | — | ✅ |
| `POST /api/auth/register` | ✅ *if* `public_registration_enabled` | — | — | ✅ (always, regardless of the setting) |
| `GET /api/export` | ❌ | ✅ (own) | — | ✅ (`?all=true`) |

## 6. Schema summary (current best guess, will evolve)

| Table | Status | Notes |
|---|---|---|
| `users` | change | `hashed_password`, `is_active`, `is_superuser`, `is_verified`, `default_recipe_locked` (bool, default `false`); drop `role` |
| `access_tokens` | new, replaces `sessions` | FastAPI Users' Database strategy shape |
| `settings` | new, ships early (§3) | `key` PK, `value`; seeded with `public_registration_enabled=true` |
| `recipes` | change | add `is_locked` boolean — value set from the creating user's `default_recipe_locked` at insert time, then independently editable per-recipe by owner/admin |
| `ingredients`, `steps`, `tags`, `recipe_tags`, `images` | unchanged | |
| `favorites` | new | `user_id` + `recipe_id` composite PK, `created_at` |
| `recipe_suggestions` | new | see §2 for full column list |

## 7. Project structure

```
backend/app/
├── core/
│   ├── config.py         # pydantic-settings: cookie name/TTL, upload dir, DATABASE_URL
│   ├── db.py               # async engine/session (asyncpg)
│   ├── users.py            # FastAPI Users wiring — UserManager, backend, fastapi_users instance
│   └── deps.py              # require_admin(), require_owner_or_admin(recipe), current_user_optional()
├── models.py                # User (FastAPI Users shape), AccessToken, Recipe (+is_locked),
│                            # Ingredient, Step, Tag, RecipeTag, Image, Favorite, RecipeSuggestion, Setting
├── schemas/
│   ├── users.py
│   ├── recipes.py            # incl. the "suggestion payload" shares this shape
│   ├── suggestions.py
│   └── settings.py
├── routers/
│   ├── users.py               # custom list/create on top of FastAPI Users
│   ├── recipes.py
│   ├── suggestions.py         # NEW
│   ├── favorites.py           # NEW
│   ├── tags.py
│   ├── settings.py            # NEW
│   └── export.py
└── main.py
```

`current_user_optional()` is worth calling out specifically: `GET /api/recipes`
and `GET /api/recipes/{id}` need a dependency that returns `None` for anonymous
requests rather than 401ing, since anonymous is a valid, supported caller for
those two routes specifically — everything else uses the normal
required-auth dependency.

## 8. Non-functional requirements

(Unchanged from the previous version — repeated briefly for completeness.)
- Dependencies: `fastapi-users[sqlalchemy]`, `asyncpg`, `httpx`,
  `pytest-asyncio`.
- Pagination: limit/offset with `total` in the response.
- Error shape: `{"detail": "..."}` everywhere.
- Rate-limit `/api/auth/cookie/login` (`slowapi`).
- Upload: size cap, content-type whitelist, server-generated UUID filenames.
- `search_vector`: Postgres trigger, not application code.
- All config via env vars (`pydantic-settings`).

## 9. Testing plan additions

Everything from the previous version still applies (async fixtures, Postgres
CI service, per-endpoint auth/ownership tests). New cases for this round:

- **Anonymous access**: `GET /api/recipes` with no cookie returns only
  non-locked recipes; `GET /api/recipes/{id}` on a locked recipe → 404 for
  anonymous, 200 for any logged-in user; anonymous gets 401/403 on every
  write endpoint, `/favorites`, and `/suggestions`.
- **Locking**: owner can lock/unlock their own recipe; non-owner user gets 403
  trying to; a newly-locked recipe disappears from anonymous list/detail but
  stays visible to logged-in users.
- **Suggestions**: non-owner can submit; owner gets 400 attempting to submit a
  suggestion on their own recipe; attempting a direct `PATCH` as a non-owner
  still 403s regardless of any pending suggestion; accept applies the
  payload's fields to the real recipe and marks status `accepted`; reject
  leaves the recipe untouched and marks `rejected`; a non-owner, non-admin
  gets 403 trying to accept/reject someone else's suggestion; author can
  withdraw their own pending suggestion but not one already resolved.
- **Favorites**: user can favorite/unfavorite; favoriting twice doesn't error
  or duplicate (idempotent, or 409 — decide and test whichever); `GET
  /api/favorites` only returns the current user's own list, never another
  user's.
- **Settings**: non-admin gets 403 on both `GET` and `PATCH`; admin changes
  persist and are reflected on subsequent `GET`.
- **Registration gating**: with `public_registration_enabled=true` (the
  default), anonymous registration succeeds; admin flips it to `false` →
  subsequent anonymous registration attempts get 403, while admin-initiated
  `POST /api/users` still works regardless of the setting.
- **Per-user lock default**: a user with `default_recipe_locked=true` creating
  a recipe gets `is_locked=true` on it automatically; changing their own
  default afterward doesn't retroactively change any existing recipe's lock
  state; a user cannot set *another* user's `default_recipe_locked` (not even
  admin — confirm this is 403/ignored on `PATCH /api/users/{id}` for that
  specific field, even though admin can otherwise edit other fields there).

## 10. Suggested implementation order

1. Async conversion of `core/db.py` + CI Postgres service + `pytest-asyncio`/
   `httpx` — confirm `/healthz` round-trips async before anything else.
2. Migration `0002`: `users` column changes (incl. `default_recipe_locked`),
   `access_tokens` table, `settings` table seeded with
   `public_registration_enabled=true`, `recipes.is_locked`. `settings` ships
   here, not later, since the custom register route depends on it existing
   from day one.
3. `core/users.py` (FastAPI Users wiring, first-user-admin logic) + the custom
   gated `POST /api/auth/register` (§3) + auth/users/registration-gating
   integration tests green before proceeding.
4. `core/deps.py`: `require_admin()`, `require_owner_or_admin()`,
   `current_user_optional()`.
5. `routers/users.py` custom list/create endpoints, incl. confirming
   `default_recipe_locked` isn't admin-editable on other users + tests.
6. `routers/settings.py` (`GET`/`PATCH`, admin only) + tests — small, but
   needed early since registration gating already depends on the table.
7. `routers/recipes.py` fully implemented: `is_locked` set from the creator's
   default at insert time, independently editable after; anonymous-vs-logged-in
   query split + tests.
8. Fold image endpoints into `recipes.py` + tests.
9. Migration `0003`: `favorites`, `recipe_suggestions` tables.
10. `routers/favorites.py` + tests.
11. `routers/suggestions.py` (submit — incl. the owner-gets-400 check —
    review/accept/reject/withdraw) + tests — this is the most novel piece,
    budget the most test-writing time here.
12. `routers/tags.py` get-or-create + tests.
13. `search_vector` trigger migration; wire `?q=` into recipes list; test search.
14. `routers/export.py` + tests.
15. Roadmap items (shopping list, URL import) — additive, don't touch existing
    contracts.
