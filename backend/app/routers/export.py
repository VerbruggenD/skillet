"""Recipe export routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.users import current_user
from ..models import Recipe, User
from .recipes import _recipe_options, _recipe_read

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export")
async def export_recipes(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
    export_all: Annotated[bool, Query(alias="all")] = False,
) -> dict[str, object]:
    """Export the current user's recipes, or all recipes for administrators."""
    statement = select(Recipe).options(*_recipe_options()).order_by(Recipe.id.asc())
    if not (export_all and user.is_superuser):
        statement = statement.where(Recipe.owner_id == user.id)
    recipes = (await session.scalars(statement)).unique().all()
    return {
        "version": 1,
        "recipes": [_recipe_read(recipe).model_dump(mode="json") for recipe in recipes],
    }
