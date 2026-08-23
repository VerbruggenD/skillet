"""User self-service and administrator user-management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi_users import exceptions
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import require_admin
from ..core.users import UserManager, current_user, get_user_manager
from ..models import User
from ..schemas.users import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


def _not_found() -> HTTPException:
    """Create the standard response for an unknown user identifier."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/me", response_model=UserRead)
async def get_me(user: Annotated[User, Depends(current_user)]) -> User:
    """Return the currently authenticated user's account."""
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    update: UserUpdate,
    request: Request,
    user: Annotated[User, Depends(current_user)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> User:
    """Update the current user's profile and recipe-lock default safely."""
    return await manager.update(update, user, safe=True, request=request)


@router.get("", response_model=list[UserRead])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> list[User]:
    """List all user accounts for an administrator."""
    return list((await session.scalars(select(User).order_by(User.id))).all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    request: Request,
    _: Annotated[User, Depends(require_admin)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> User:
    """Allow an administrator to create an account even when registration is closed."""
    try:
        return await manager.create(user_create, safe=False, request=request)
    except exceptions.UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        ) from exc


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    _: Annotated[User, Depends(require_admin)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> User:
    """Return an account by identifier for an administrator."""
    try:
        return await manager.get(user_id)
    except exceptions.UserNotExists as exc:
        raise _not_found() from exc


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    update: UserUpdate,
    request: Request,
    _: Annotated[User, Depends(require_admin)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> User:
    """Update an account while preserving its personal recipe-lock preference."""
    if "default_recipe_locked" in update.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="default_recipe_locked can only be changed by its owner",
        )
    try:
        user = await manager.get(user_id)
    except exceptions.UserNotExists as exc:
        raise _not_found() from exc
    return await manager.update(update, user, safe=False, request=request)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    _: Annotated[User, Depends(require_admin)],
    manager: Annotated[UserManager, Depends(get_user_manager)],
) -> Response:
    """Delete an account as an administrator."""
    try:
        user = await manager.get(user_id)
    except exceptions.UserNotExists as exc:
        raise _not_found() from exc
    await manager.delete(user, request=request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
