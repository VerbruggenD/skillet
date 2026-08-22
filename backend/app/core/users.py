"""FastAPI Users integration and auth dependency wiring for the API."""

from collections.abc import AsyncIterator
from typing import Annotated, Any, cast

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from .db import get_db


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Handle password reset, verification, and user lifecycle operations."""

    reset_password_token_secret = "change-me"
    verification_token_secret = "change-me"


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncIterator[SQLAlchemyUserDatabase[User, int]]:
    """Build a user database adapter scoped to the current request session."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase[User, int], Depends(get_user_db)],
) -> AsyncIterator[UserManager]:
    """Create the user manager for the active request with the current database adapter."""
    yield UserManager(user_db)


cookie_transport = CookieTransport(cookie_name="skillet-session", cookie_max_age=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=lambda: cast(Any, None),
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user()
current_user_optional = fastapi_users.current_user(optional=True)
