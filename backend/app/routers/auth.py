"""Authentication routes for login, logout, registration, and current-user lookup."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import exceptions
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.settings import get_public_registration_enabled
from ..core.users import UserManager, current_user_optional, get_user_manager
from ..models import User
from ..schemas.users import UserCreate, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user_optional)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> UserRead:
    """Gate registration with the instance policy before creating an account.

    The account creation step belongs to the auth/user implementation; the
    policy check is intentionally kept here so that route uses the persisted
    instance setting rather than an environment-time configuration value.
    """
    registration_open = await get_public_registration_enabled(session)
    if not registration_open and (user is None or not user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled",
        )
    try:
        created_user = await manager.create(user_create, safe=True, request=request)
    except exceptions.UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        ) from exc
    return UserRead.model_validate(created_user)
