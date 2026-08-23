"""Reusable authorization dependencies for API routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from ..models import User
from .users import current_user


async def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    """Return the current user when they have instance administrator privileges."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user
