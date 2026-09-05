"""Behavior tests for authentication rate limiting."""

import os
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rate_limit import limiter
from app.core.users import get_database_strategy, get_user_manager
from app.main import app

client = TestClient(app)


class FakeUserManager:
    """Authentication double that returns invalid credentials without a database."""

    async def authenticate(self, _: object) -> None:
        """Return no user so the request reaches normal login failure handling."""
        return None


def test_cookie_login_is_rate_limited() -> None:
    """The sixth login attempt from one client is rejected with HTTP 429."""
    limiter.reset()
    app.dependency_overrides[get_user_manager] = lambda: FakeUserManager()
    app.dependency_overrides[get_database_strategy] = lambda: SimpleNamespace()
    try:
        responses = [
            client.post(
                "/api/auth/cookie/login",
                data={"username": "user@example.com", "password": "wrong"},
            )
            for _ in range(6)
        ]
        assert [response.status_code for response in responses[:5]] == [400] * 5
        assert responses[5].status_code == 429
    finally:
        limiter.reset()
        app.dependency_overrides.clear()
