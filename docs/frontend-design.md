# Skillet — Frontend Design Plan

Based on `docs/design.md`: Next.js/React frontend, FastAPI backend, three-tier
roles (admin / user / viewer), and the five feature pillars — core CRUD,
recipe editor, cook mode, browsing/search, import/export.

---

## 1. Page inventory

| Route | Page | Auth | Purpose |
|---|---|---|---|
| `/login` | Login | public | Email/password sign-in |
| `/register` | Register | public (or admin-invite only) | Create account |
| `/` | Recipe browse | user+ | Grid/list of all visible recipes, entry point |
| `/recipes/[id]` | Recipe detail | user+ | Read view — ingredients, steps, image, tags, "Cook" button |
| `/recipes/new` | Recipe editor (create) | user+ | Structured create form |
| `/recipes/[id]/edit` | Recipe editor (edit) | owner/admin | Structured edit form, prefilled |
| `/recipes/import` | Import from URL | user+ | Paste URL → parsed preview → opens in editor |
| `/recipes/[id]/cook` | Cook mode | user+ | Full-screen step-by-step view |
| `/shopping-list` | Shopping list builder | user+ | Pick recipes → merged ingredient list |
| `/tags/[tag]` | Tag view | user+ | Recipes filtered by one tag (optional — could just be a browse filter param) |
| `/account` | Account settings | user+ | Change password, view role |
| `/admin/users` | User management | admin | List/edit users and roles |
| `/export` | Export | user+ | Trigger/download JSON export |

Note: several of these (tag view, export) could be modals or panels rather than
full routes — decide per your appetite for URL-addressable state vs simplicity.

---

## 2. Global / shared components

- **AppShell** — header, nav, auth-aware menu (login/logout, account link, admin link if role=admin)
- **SearchBar** — text input + tag multi-select, used on browse and possibly header
- **RecipeCard** — image, title, tags, prep/cook time; used in grid & list views
- **TagPill / TagPicker** — display and multi-select input for tags
- **ServingsStepper** — +/- control that drives quantity scaling, reused on detail + cook mode
- **ImageUploader** — drag-and-drop + file picker, preview thumbnail, used in editor
- **ConfirmDialog** — generic "are you sure?" for delete actions
- **Toast/Notification** — save success, errors, autosave status
- **LoadingSkeletons** — for recipe grid, detail, editor while fetching
- **AuthGuard / RoleGuard** — route wrapper redirecting unauthenticated/unauthorized users
- **ApiClient** — thin wrapper around fetch with cookie-based auth, typed against the OpenAPI schema

---

## 3. Page-by-page feature breakdown

### Recipe browse (`/`)
- Grid/list toggle
- Sort: name, date added, prep time, last cooked
- Filter: tags (multi), search text, max prep time
- Pagination (matches whatever the API decides — offset or cursor)
- Empty state ("no recipes yet — add one")
- Responsive: grid collapses to single column on mobile

### Recipe detail (`/recipes/[id]`)
- Title, description, image(s)
- Ingredients list (servings-aware, scaled client-side via ServingsStepper)
- Steps list (read-only, numbered)
- Tags
- Prep/cook time, servings
- Actions: Edit (if owner/admin), Delete (with confirm), Start Cooking, Add to shopping list
- Owner attribution if shared-cookbook mode is on

### Recipe editor (`/recipes/new`, `/recipes/[id]/edit`)
- Title, description, prep/cook time, servings, source URL fields
- Ingredients sub-form: add/remove/reorder rows (name, quantity, unit) — drag-and-drop reorder
- Steps sub-form: add/remove/reorder ordered instruction rows
- Tag picker (create-on-the-fly or select existing)
- Image uploader with preview
- Live preview pane (renders as it will look in detail/cook views)
- Autosave indicator or explicit "Save draft" button
- Validation: required title, at least one ingredient/step before publish

### Import from URL (`/recipes/import`)
- URL input field
- Parse button → loading state → preview of parsed fields
- "Edit before saving" → hands off directly into the editor pre-filled
- Error state for URLs without valid `schema.org/Recipe` data

### Cook mode (`/recipes/[id]/cook`)
- Full-screen, minimal chrome layout (separate layout, not AppShell)
- One step at a time, large text
- Next/previous controls (button, swipe, arrow keys)
- Ingredient checklist panel (toggle open/closed), checkable items
- Inline timer component triggered by steps with a duration; alert/sound on completion
- Wake Lock API call on mount, released on unmount, with feature-detection fallback
- Respects servings scaling chosen before entering cook mode
- Exit control back to detail page

### Shopping list (`/shopping-list`)
- Multi-select recipe picker (search + checkboxes)
- Generated list: merged, deduplicated, unit-aware quantities
- Manual check-off per item
- Optional: copy-to-clipboard or print view

### Account (`/account`)
- Change password form
- Display current role
- Logout

### Admin — user management (`/admin/users`)
- Table: email, role, created date
- Edit role, delete/disable user
- Guarded by `require_role('admin')` equivalent on the frontend route + backend enforcement

### Export (`/export`)
- Button hitting the export endpoint, triggers file download

---

## 4. Cross-cutting concerns

- **Auth/session context** — global React context holding current user + role, populated from `GET /api/auth/me` on load; drives AuthGuard/RoleGuard and conditional nav items.
- **API client layer** — typed wrapper (can codegen from FastAPI's OpenAPI schema) so editor/detail/browse all share request/response types instead of hand-rolled fetches.
- **Serving-size scaling logic** — implement once as a shared utility (recipe + servings → scaled ingredient list), consumed by both detail page and cook mode per the design doc's explicit call-out to avoid duplication.
- **Responsive design** — mobile/tablet is a first-class target (kitchen use case), not an afterthought; test browse and cook mode on a narrow viewport from the start.
- **Error/loading states** — consistent pattern across pages (skeleton while loading, toast on error) rather than one-off handling per page.
- **Design tokens** — pick a small set (spacing scale, type scale, one accent color, light/dark if desired) before building components, so RecipeCard/buttons/forms stay visually consistent without re-deciding per component.

---

## 5. Suggested build order (matches backend's suggested order)

1. AppShell + auth context + login/register pages, wired to real auth endpoints
2. Recipe browse (grid/list, basic fetch) + Recipe detail (read-only) — proves the full request path
3. Recipe editor (structured forms, image upload, autosave) — the biggest single chunk of frontend work
4. Browsing polish — sort, filter combos, responsive pass
5. Cook mode — full-screen view, checklist, timers, wake lock
6. Search + tag filtering wired into browse
7. Serving size scaling (shared utility) — retrofit into detail + cook mode
8. Shopping list page
9. Import-from-URL flow → editor handoff
10. Account page, admin user management, export button

This mirrors the backend's step-by-step so each frontend milestone lands against
an API surface that's already stubbed or implemented.
