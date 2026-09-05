"""Behavior tests for tags, recipe search filters, and export."""

import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.db import get_db
from app.core.users import current_user, current_user_optional
from app.main import app
from app.models import Recipe, Tag

client = TestClient(app)


class FakeResult:
    """Minimal result object for SQLAlchemy collection queries."""

    def __init__(self, items: list[Any]) -> None:
        """Store query rows."""
        self.items = items

    def unique(self) -> "FakeResult":
        """Match SQLAlchemy's unique result method."""
        return self

    def all(self) -> list[Any]:
        """Return query rows."""
        return self.items


class FakeSearchSession:
    """Session double for tag writes, tag listing, and export reads."""

    def __init__(
        self, *, scalar_values: list[Any] | None = None, rows: list[Any] | None = None
    ) -> None:
        """Configure scalar and collection query results."""
        self.scalar_values = list(scalar_values or [])
        self.rows = rows or []
        self.added: list[Any] = []
        self.commits = 0

    async def scalar(self, _: Any) -> Any:
        """Return the next configured scalar result."""
        return self.scalar_values.pop(0) if self.scalar_values else None

    async def scalars(self, _: Any) -> FakeResult:
        """Return configured collection rows."""
        return FakeResult(self.rows)

    def add(self, value: Any) -> None:
        """Capture persisted objects and provide generated fields."""
        self.added.append(value)
        if isinstance(value, Recipe):
            value.id = 10
            value.created_at = datetime.now(timezone.utc)
            for index, step in enumerate(value.steps, start=1):
                step.id = index
            for index, ingredient in enumerate(value.ingredients, start=1):
                ingredient.id = index
        if isinstance(value, Tag):
            value.id = len([item for item in self.added if isinstance(item, Tag)])

    async def refresh(self, recipe: Recipe, attribute_names: Any = None) -> None:
        """Provide loaded child collections for recipe serialization."""
        recipe.ingredients = list(recipe.ingredients)
        recipe.steps = list(recipe.steps)
        recipe.images = list(recipe.images)
        recipe.tags = list(recipe.tags)

    async def commit(self) -> None:
        """Record a successful transaction."""
        self.commits += 1

    async def delete(self, _: Any) -> None:
        """Accept tag deletion requests."""


def make_recipe(owner_id: int = 1, title: str = "Soup") -> Recipe:
    """Build an eagerly loaded recipe for export responses."""
    recipe = Recipe(
        id=10,
        owner_id=owner_id,
        title=title,
        description="A warm soup",
        servings=4,
        is_locked=False,
        created_at=datetime.now(timezone.utc),
    )
    recipe.ingredients = []
    recipe.steps = []
    recipe.images = []
    recipe.tags = [Tag(id=1, name="quick")]
    return recipe


def override_db(session: FakeSearchSession, user: Any = None) -> None:
    """Install database and authentication overrides for a test."""

    async def get_test_db() -> Any:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[current_user_optional] = lambda: user


def test_recipe_creation_normalizes_and_reuses_tags() -> None:
    """Recipe writes normalize tag names to lowercase and create each distinct tag once."""
    session = FakeSearchSession(scalar_values=[None])
    user = SimpleNamespace(id=1, default_recipe_locked=False, is_superuser=False)
    override_db(session, user)
    try:
        response = client.post(
            "/api/recipes",
            json={"title": "Soup", "tags": [" Quick ", "quick", "Dinner"]},
        )
        assert response.status_code == 201
        tags = [item for item in session.added if isinstance(item, Tag)]
        assert [tag.name for tag in tags] == ["quick", "dinner"]
        recipe = next(item for item in session.added if isinstance(item, Recipe))
        assert [tag.name for tag in recipe.tags] == ["quick", "dinner"]
    finally:
        app.dependency_overrides.clear()


def test_tag_listing_is_public_and_sorted() -> None:
    """Anonymous callers can retrieve tags in name order."""
    session = FakeSearchSession(rows=[Tag(id=2, name="quick"), Tag(id=1, name="dinner")])
    override_db(session)
    try:
        response = client.get("/api/tags")
        assert response.status_code == 200
        assert [tag["name"] for tag in response.json()] == ["quick", "dinner"]
    finally:
        app.dependency_overrides.clear()


def test_recipe_search_filters_are_accepted() -> None:
    """Recipe listing accepts full-text, tag, sort, and pagination filters."""
    session = FakeSearchSession(rows=[make_recipe()])
    override_db(session)
    try:
        response = client.get(
            "/api/recipes",
            params={"q": "soup", "tag": "quick", "sort": "name", "page": 1, "limit": 10},
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["tags"] == [{"id": 1, "name": "quick"}]
    finally:
        app.dependency_overrides.clear()


def test_user_export_contains_only_the_current_users_recipes() -> None:
    """A normal user receives a complete export response for their scoped query."""
    session = FakeSearchSession(rows=[make_recipe(owner_id=2)])
    override_db(session, SimpleNamespace(id=2, is_superuser=False))
    try:
        response = client.get("/api/export")
        assert response.status_code == 200
        assert response.json()["version"] == 1
        assert [recipe["title"] for recipe in response.json()["recipes"]] == ["Soup"]
        assert response.json()["recipes"][0]["tags"] == [{"id": 1, "name": "quick"}]
    finally:
        app.dependency_overrides.clear()


def test_admin_all_export_returns_the_admin_scoped_query() -> None:
    """Administrators can request the all-recipes export variant."""
    session = FakeSearchSession(
        rows=[make_recipe(owner_id=1), make_recipe(owner_id=2, title="Stew")]
    )
    override_db(session, SimpleNamespace(id=1, is_superuser=True))
    try:
        response = client.get("/api/export?all=true")
        assert response.status_code == 200
        assert [recipe["title"] for recipe in response.json()["recipes"]] == ["Soup", "Stew"]
    finally:
        app.dependency_overrides.clear()
