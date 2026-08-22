"""Behavior tests for the minimal backend API surface."""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok() -> None:
    """The health check endpoint should report the backend is available."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_routes_are_not_implemented_yet() -> None:
    """The auth placeholders should clearly report they are still pending."""
    response = client.get("/api/auth/me")

    assert response.status_code == 501
    assert response.json() == {"detail": "Not implemented: me"}


def test_recipe_image_upload_requires_a_file() -> None:
    """The recipe image route should reject uploads without a file body."""
    response = client.post("/api/recipes/1/image")

    assert response.status_code == 400
    assert response.json() == {"detail": "File is required"}


def test_tag_listing_returns_placeholder_not_implemented() -> None:
    """The tag endpoint should remain explicit while the feature is pending."""
    response = client.get("/api/tags/")

    assert response.status_code == 501
    assert response.json() == {"detail": "Not implemented: list tags"}
