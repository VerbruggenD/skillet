"""Behavior tests for the minimal backend API surface."""

import os
import sys
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.db import get_db
from app.core.users import current_user, current_user_optional
from app.main import app
from app.models import Setting

client = TestClient(app)


class FakeSettingsSession:
    """Small in-memory session double for settings route behavior tests."""

    def __init__(self) -> None:
        """Start with no persisted settings."""
        self.setting: Setting | None = None
        self.commits = 0

    async def scalar(self, _: Any) -> Setting | None:
        """Return the single supported setting."""
        return self.setting

    def add(self, setting: Setting) -> None:
        """Store a setting as an ORM session would before committing."""
        self.setting = setting

    async def commit(self) -> None:
        """Record a successful persistence operation."""
        self.commits += 1


def test_settings_are_admin_only_and_persisted() -> None:
    """Only administrators may read or change the registration policy."""
    session = FakeSettingsSession()

    async def get_test_db() -> Any:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(is_superuser=False)
    try:
        assert client.get("/api/settings").status_code == 403
        response = client.patch(
            "/api/settings",
            json={"public_registration_enabled": False},
        )
        assert response.status_code == 403

        app.dependency_overrides[current_user] = lambda: SimpleNamespace(is_superuser=True)
        response = client.get("/api/settings")
        assert response.status_code == 200
        assert response.json() == {"public_registration_enabled": True}

        response = client.patch(
            "/api/settings",
            json={"public_registration_enabled": False},
        )
        assert response.status_code == 200
        assert response.json() == {"public_registration_enabled": False}
        assert session.setting is not None
        assert session.setting.value == "false"
        assert session.commits == 1
    finally:
        app.dependency_overrides.clear()


def test_registration_is_blocked_when_public_registration_is_disabled() -> None:
    """The persisted registration setting rejects anonymous sign-ups when closed."""
    session = FakeSettingsSession()
    session.setting = Setting(key="public_registration_enabled", value="false")

    async def get_test_db() -> Any:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[current_user_optional] = lambda: None
    try:
        response = client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "safe-password"},
        )

        assert response.status_code == 403
        assert response.json() == {"detail": "Public registration is disabled"}
    finally:
        app.dependency_overrides.clear()


def test_healthz_returns_ok() -> None:
    """The health check endpoint should report the backend is available."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_profile_requires_authentication() -> None:
    """The completed user profile route should reject unauthenticated callers."""
    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_auth_and_user_routes_match_the_api_contract() -> None:
    """Authentication and user-management routes are exposed at their designed paths."""
    openapi = app.openapi()["paths"]

    assert {"post"} <= set(openapi["/api/auth/cookie/login"])
    assert {"post"} <= set(openapi["/api/auth/cookie/logout"])
    assert {"post"} <= set(openapi["/api/auth/register"])
    assert {"get", "patch"} <= set(openapi["/api/users/me"])
    assert {"get", "post"} <= set(openapi["/api/users"])
    assert {"get", "patch", "delete"} <= set(openapi["/api/users/{user_id}"])


def test_recipe_image_upload_requires_authentication() -> None:
    """The recipe image route should reject an unauthenticated upload request."""
    response = client.post("/api/recipes/1/image")

    assert response.status_code == 401


def test_tag_routes_match_the_api_contract() -> None:
    """Tag listing is public and tag deletion is administrator-only."""
    openapi = app.openapi()["paths"]

    assert {"get"} <= set(openapi["/api/tags"])
    assert {"delete"} <= set(openapi["/api/tags/{tag_id}"])


def test_search_and_export_routes_match_the_api_contract() -> None:
    """Recipe search filters and authenticated export are exposed."""
    openapi = app.openapi()["paths"]
    recipe_query_names = {
        parameter["name"] for parameter in openapi["/api/recipes"]["get"]["parameters"]
    }

    assert {"q", "tag", "sort", "page", "limit"} <= recipe_query_names
    assert {"get"} <= set(openapi["/api/export"])


def test_export_requires_authentication() -> None:
    """Recipe export is not available to anonymous callers."""
    response = client.get("/api/export")
    assert response.status_code == 401
