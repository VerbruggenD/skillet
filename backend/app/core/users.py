"""FastAPI Users integration and auth dependency wiring for the API."""

from collections.abc import AsyncIterator
from typing import Annotated, Any, cast

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AccessToken, User
from .config import settings
from .db import get_db


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Handle password reset, verification, and user lifecycle operations."""

    reset_password_token_secret = "change-me"
    verification_token_secret = "change-me"

    async def on_after_register(self, user: User, request: object | None = None) -> None:
        """Promote the first registered account to instance administrator."""
        user_db = cast(SQLAlchemyUserDatabase[User, int], self.user_db)
        session = user_db.session
        user_count = await session.scalar(select(func.count()).select_from(User))
        if user_count == 1:
            await self.user_db.update(user, {"is_superuser": True})


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


async def get_access_token_db(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncIterator[SQLAlchemyAccessTokenDatabase[Any]]:
    """Build an access-token adapter scoped to the active request session."""
    token_db = SQLAlchemyAccessTokenDatabase(session, AccessToken)
    yield cast(SQLAlchemyAccessTokenDatabase[Any], token_db)


async def get_database_strategy(
    access_token_db: Annotated[SQLAlchemyAccessTokenDatabase[Any], Depends(get_access_token_db)],
) -> DatabaseStrategy[User, int, Any]:
    """Use opaque, server-side access tokens with the configured cookie lifetime."""
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)


cookie_transport = CookieTransport(
    cookie_name=settings.cookie_name,
    cookie_max_age=3600,
    cookie_secure=settings.cookie_secure,
)


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_database_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user()
current_user_optional = fastapi_users.current_user(optional=True)
