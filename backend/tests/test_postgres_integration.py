"""Opt-in API integration tests against a real PostgreSQL database."""

import asyncio
import os
import sys
from collections.abc import AsyncIterator, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.db import get_db
from app.main import app
from app.models import User

TEST_DATABASE_URL = os.environ.get("SKILLET_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="SKILLET_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.fixture
def database_sessionmaker() -> Iterator[async_sessionmaker[AsyncSession]]:
    """Provide a real PostgreSQL session factory for the test request lifecycle."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def get_test_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    try:
        yield sessionmaker
    finally:
        app.dependency_overrides.clear()


def test_recipe_api_round_trip_uses_postgres(
    database_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Exercise auth, recipe writes, search, export, and locked visibility in Postgres."""
    email = f"integration-{uuid4()}@example.com"
    password = "integration-password"
    with TestClient(app) as client:
        registration = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "default_recipe_locked": True},
        )
        assert registration.status_code == 201

        login = client.post(
            "/api/auth/cookie/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 204

        created = client.post(
            "/api/recipes",
            json={
                "title": "Postgres Soup",
                "description": "A searchable integration recipe",
                "ingredients": [{"name": "pepper", "quantity": 1, "unit": " tsp"}],
                "steps": [{"instruction": "Stir the pepper"}],
                "tags": [" Integration ", "search"],
            },
        )
        assert created.status_code == 201
        recipe = created.json()
        assert recipe["is_locked"] is True
        assert [tag["name"] for tag in recipe["tags"]] == ["integration", "search"]

        search = client.get("/api/recipes", params={"q": "pepper", "tag": "search"})
        assert search.status_code == 200
        assert [item["id"] for item in search.json()["items"]] == [recipe["id"]]

        export = client.get("/api/export")
        assert export.status_code == 200
        assert export.json()["recipes"][0]["id"] == recipe["id"]

        with TestClient(app) as anonymous:
            public_detail = anonymous.get(f"/api/recipes/{recipe['id']}")
            assert public_detail.status_code == 404

    try:

        async def remove_test_user() -> None:
            assert TEST_DATABASE_URL is not None
            engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
            async with async_sessionmaker(engine, class_=AsyncSession)() as session:
                await session.execute(delete(User).where(User.email == email))
                await session.commit()
            await engine.dispose()

        asyncio.run(remove_test_user())
    finally:
        app.dependency_overrides.clear()
