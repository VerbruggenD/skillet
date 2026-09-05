"""Behavior tests for recipe suggestions and favorites."""

import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.db import get_db
from app.core.users import current_user
from app.main import app
from app.models import Favorite, Recipe, RecipeSuggestion

client = TestClient(app)


class FakeResult:
    """Minimal result object for SQLAlchemy collection queries."""

    def __init__(self, items: list[Any]) -> None:
        """Store the rows returned by a query."""
        self.items = items

    def unique(self) -> "FakeResult":
        """Match SQLAlchemy's unique result method."""
        return self

    def all(self) -> list[Any]:
        """Return the stored rows."""
        return self.items


class FakeSession:
    """Queue-based session double for suggestion and favorite routes."""

    def __init__(
        self, *, scalar_values: list[Any] | None = None, rows: list[Any] | None = None
    ) -> None:
        """Configure scalar and collection query results."""
        self.scalar_values = list(scalar_values or [])
        self.rows = rows or []
        self.added: Any = None
        self.commits = 0
        self.deleted: Any = None

    async def scalar(self, _: Any) -> Any:
        """Return the next configured scalar result."""
        return self.scalar_values.pop(0) if self.scalar_values else None

    async def scalars(self, _: Any) -> FakeResult:
        """Return configured collection rows."""
        return FakeResult(self.rows)

    def add(self, value: Any) -> None:
        """Capture additions and provide database-generated values."""
        self.added = value
        if isinstance(value, RecipeSuggestion):
            value.id = 9
            value.created_at = datetime.now(timezone.utc)
        if isinstance(value, Favorite):
            value.created_at = datetime.now(timezone.utc)

    async def refresh(self, _: Any) -> None:
        """Accept refresh calls after persistence."""

    async def commit(self) -> None:
        """Record a successful commit."""
        self.commits += 1

    async def delete(self, value: Any) -> None:
        """Capture a deletion request."""
        self.deleted = value

    async def execute(self, _: Any) -> None:
        """Accept bulk delete statements used by favorite removal."""
        self.commits += 1


def make_recipe(owner_id: int = 1) -> Recipe:
    """Create an eagerly loaded recipe for route responses."""
    recipe = Recipe(
        id=3,
        owner_id=owner_id,
        title="Soup",
        is_locked=False,
        created_at=datetime.now(timezone.utc),
    )
    recipe.ingredients = []
    recipe.steps = []
    recipe.images = []
    return recipe


def override_db(session: FakeSession, user: Any) -> None:
    """Install database and authentication overrides for a test."""

    async def get_test_db() -> Any:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[current_user] = lambda: user


def test_anonymous_cannot_favorite() -> None:
    """Favorite writes require authentication."""
    response = client.post("/api/recipes/3/favorite")
    assert response.status_code == 401


def test_favorite_is_idempotent() -> None:
    """Favoriting an already-favorited recipe does not create a duplicate."""
    session = FakeSession(scalar_values=[make_recipe(), None])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.post("/api/recipes/3/favorite")
        assert response.status_code == 204
        assert isinstance(session.added, Favorite)
        assert session.added.user_id == 2
        assert session.commits == 1
    finally:
        app.dependency_overrides.clear()


def test_favorites_are_scoped_to_current_user() -> None:
    """Favorite listing returns only rows supplied for the current user query."""
    recipe = make_recipe()
    session = FakeSession(rows=[recipe])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.get("/api/favorites")
        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == 3
    finally:
        app.dependency_overrides.clear()


def test_recipe_owner_cannot_submit_suggestion() -> None:
    """Owners must edit their recipes directly instead of suggesting changes."""
    session = FakeSession(scalar_values=[make_recipe(owner_id=2)])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.post(
            "/api/recipes/3/suggestions",
            json={"payload": {"title": "New soup"}},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Owners must edit their own recipes directly"}
    finally:
        app.dependency_overrides.clear()


def test_non_owner_can_submit_suggestion() -> None:
    """A different authenticated user can submit a validated recipe proposal."""
    session = FakeSession(scalar_values=[make_recipe(owner_id=1)])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.post(
            "/api/recipes/3/suggestions",
            json={"payload": {"title": "New soup"}, "note": "Less salt"},
        )
        assert response.status_code == 201
        assert isinstance(session.added, RecipeSuggestion)
        assert session.added.payload == {"title": "New soup"}
        assert session.added.status == "pending"
    finally:
        app.dependency_overrides.clear()


def test_owner_accepts_suggestion_and_applies_payload() -> None:
    """Accepting a suggestion updates the recipe and resolves the suggestion."""
    recipe = make_recipe(owner_id=1)
    suggestion = RecipeSuggestion(
        id=9,
        recipe_id=3,
        suggested_by=2,
        payload={"title": "New soup"},
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session = FakeSession(scalar_values=[recipe, suggestion])
    override_db(session, SimpleNamespace(id=1, is_superuser=False))
    try:
        response = client.post("/api/recipes/3/suggestions/9/accept")
        assert response.status_code == 200
        assert recipe.title == "New soup"
        assert suggestion.status == "accepted"
        assert suggestion.resolved_by == 1
    finally:
        app.dependency_overrides.clear()


def test_non_reviewer_cannot_accept_suggestion() -> None:
    """Only the recipe owner or an administrator can resolve suggestions."""
    recipe = make_recipe(owner_id=1)
    suggestion = RecipeSuggestion(
        id=9,
        recipe_id=3,
        suggested_by=2,
        payload={"title": "New soup"},
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session = FakeSession(scalar_values=[recipe, suggestion])
    override_db(session, SimpleNamespace(id=4, is_superuser=False))
    try:
        response = client.post("/api/recipes/3/suggestions/9/accept")
        assert response.status_code == 403
        assert suggestion.status == "pending"
    finally:
        app.dependency_overrides.clear()


def test_author_can_withdraw_pending_suggestion() -> None:
    """A suggestion author can withdraw their own pending proposal."""
    suggestion = RecipeSuggestion(
        id=9,
        recipe_id=3,
        suggested_by=2,
        payload={"title": "New soup"},
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    session = FakeSession(scalar_values=[suggestion])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.delete("/api/recipes/3/suggestions/9")
        assert response.status_code == 204
        assert session.deleted is None
        assert suggestion.status == "withdrawn"
        assert suggestion.resolved_by == 2
    finally:
        app.dependency_overrides.clear()
