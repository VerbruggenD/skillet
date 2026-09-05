"""Focused behavior tests for recipe lifecycle routes."""

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
from app.models import Recipe

client = TestClient(app)


class FakeScalarResult:
    """Minimal async scalar result used by recipe route tests."""

    def __init__(self, items: list[Recipe]) -> None:
        """Store rows returned by a collection query."""
        self.items = items

    def unique(self) -> "FakeScalarResult":
        """Match SQLAlchemy's unique result method."""
        return self

    def all(self) -> list[Recipe]:
        """Return the stored rows."""
        return self.items


class FakeRecipeSession:
    """Small session double covering the recipe route persistence calls."""

    def __init__(self, recipe: Recipe | None = None, total: int = 0) -> None:
        """Configure the recipe returned by scalar queries."""
        self.recipe = recipe
        self.total = total
        self.added: Recipe | None = None
        self.commits = 0

    async def scalar(self, statement: Any) -> Recipe | int | None:
        """Return a count for list queries or the configured recipe for detail queries."""
        if self.recipe is None and self.total:
            return self.total
        if self.recipe is not None and "count" in str(statement).lower():
            return self.total
        return self.recipe

    async def scalars(self, statement: Any) -> FakeScalarResult:
        """Return the configured recipe as a collection result."""
        return FakeScalarResult([self.recipe] if self.recipe is not None else [])

    def add(self, recipe: Recipe) -> None:
        """Capture a newly created recipe and provide database-generated fields."""
        self.added = recipe
        recipe.id = 1
        recipe.created_at = datetime.now(timezone.utc)
        for index, ingredient in enumerate(recipe.ingredients, start=1):
            ingredient.id = index
        for index, step in enumerate(recipe.steps, start=1):
            step.id = index

    async def refresh(self, recipe: Recipe, attribute_names: Any = None) -> None:
        """Provide the loaded child collections expected by the response serializer."""
        recipe.ingredients = list(recipe.ingredients)
        recipe.steps = list(recipe.steps)
        recipe.images = list(recipe.images)

    async def commit(self) -> None:
        """Record a successful transaction."""
        self.commits += 1

    async def delete(self, recipe: Recipe) -> None:
        """Accept deletion requests from the route."""
        self.recipe = None


def make_recipe(*, owner_id: int = 1, locked: bool = False) -> Recipe:
    """Build a fully loaded recipe suitable for response serialization."""
    recipe = Recipe(
        id=1,
        owner_id=owner_id,
        title="Soup",
        description="A warm soup",
        servings=4,
        is_locked=locked,
        created_at=datetime.now(timezone.utc),
    )
    recipe.ingredients = []
    recipe.steps = []
    recipe.images = []
    return recipe


def set_overrides(session: FakeRecipeSession, *, user: Any = None) -> None:
    """Install the database and authentication doubles for one test."""

    async def get_test_db() -> Any:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[current_user_optional] = lambda: user


def test_anonymous_recipe_list_exposes_only_public_rows() -> None:
    """Anonymous collection reads return the public recipe subset."""
    session = FakeRecipeSession(make_recipe(), total=1)
    set_overrides(session)
    try:
        response = client.get("/api/recipes")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert len(response.json()["items"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_anonymous_locked_recipe_is_not_found() -> None:
    """Anonymous detail reads cannot discover locked recipes."""
    session = FakeRecipeSession(make_recipe(locked=True))
    set_overrides(session)
    try:
        response = client.get("/api/recipes/1")
        assert response.status_code == 404
        assert response.json() == {"detail": "Recipe not found"}
    finally:
        app.dependency_overrides.clear()


def test_create_recipe_applies_user_lock_default() -> None:
    """New recipes inherit the creator's current lock preference."""
    session = FakeRecipeSession()
    user = SimpleNamespace(id=7, default_recipe_locked=True, is_superuser=False)
    set_overrides(session, user=user)
    try:
        response = client.post(
            "/api/recipes",
            json={"title": "Soup", "steps": [{"instruction": "Stir"}]},
        )
        assert response.status_code == 201
        assert session.added is not None
        assert session.added.owner_id == 7
        assert session.added.is_locked is True
        assert response.json()["steps"][0]["order"] == 1
    finally:
        app.dependency_overrides.clear()


def test_non_owner_cannot_update_recipe() -> None:
    """A regular user cannot modify another user's recipe."""
    session = FakeRecipeSession(make_recipe(owner_id=1))
    user = SimpleNamespace(id=2, default_recipe_locked=False, is_superuser=False)
    set_overrides(session, user=user)
    try:
        response = client.patch("/api/recipes/1", json={"is_locked": True})
        assert response.status_code == 403
        assert response.json() == {"detail": "Recipe owner or administrator required"}
        assert session.commits == 0
    finally:
        app.dependency_overrides.clear()


def test_admin_can_update_recipe_lock() -> None:
    """An administrator can change a recipe's lock state regardless of owner."""
    recipe = make_recipe(owner_id=1)
    session = FakeRecipeSession(recipe)
    user = SimpleNamespace(id=2, default_recipe_locked=False, is_superuser=True)
    set_overrides(session, user=user)
    try:
        response = client.patch("/api/recipes/1", json={"is_locked": True})
        assert response.status_code == 200
        assert recipe.is_locked is True
        assert session.commits == 1
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_can_record_a_cook() -> None:
    """Cooking a recipe updates its last-cooked timestamp."""
    recipe = make_recipe(owner_id=1)
    session = FakeRecipeSession(recipe)
    user = SimpleNamespace(id=2, default_recipe_locked=False, is_superuser=False)
    set_overrides(session, user=user)
    try:
        response = client.post("/api/recipes/1/cook")
        assert response.status_code == 200
        assert recipe.last_cooked is not None
        assert response.json()["last_cooked"] is not None
        assert session.commits == 1
    finally:
        app.dependency_overrides.clear()


def test_image_upload_rejects_unsupported_content_type() -> None:
    """Recipe image uploads accept only the configured image content types."""
    session = FakeRecipeSession(make_recipe())
    user = SimpleNamespace(id=1, default_recipe_locked=False, is_superuser=False)
    set_overrides(session, user=user)
    try:
        response = client.post(
            "/api/recipes/1/image",
            files={"file": ("recipe.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 415
        assert response.json() == {"detail": "Unsupported image type"}
    finally:
        app.dependency_overrides.clear()
