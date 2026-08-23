"""Schemas for registration and user-management endpoints."""

from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """The public representation of a user account."""

    default_recipe_locked: bool = False


class UserCreate(schemas.BaseUserCreate):
    """Fields accepted when creating an account."""

    default_recipe_locked: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    """Fields a user may update on their own account."""

    default_recipe_locked: bool | None = None
