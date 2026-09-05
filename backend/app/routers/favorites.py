"""Favorite recipe routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.users import current_user
from ..models import Favorite, Recipe, User
from ..schemas.recipes import RecipeList
from .recipes import _recipe_options, _recipe_read

router = APIRouter(prefix="/api", tags=["favorites"])


async def _get_recipe(session: AsyncSession, recipe_id: int) -> Recipe:
    """Fetch a recipe for favorite operations."""
    recipe = await session.scalar(
        select(Recipe).where(Recipe.id == recipe_id).options(*_recipe_options())
    )
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.get("/favorites", response_model=RecipeList)
async def list_favorites(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeList:
    """List only the recipes favorited by the current user."""
    statement = (
        select(Recipe)
        .join(Favorite, Favorite.recipe_id == Recipe.id)
        .where(Favorite.user_id == user.id)
        .options(*_recipe_options())
        .order_by(Favorite.created_at.desc(), Recipe.id.desc())
    )
    recipes = (await session.scalars(statement)).unique().all()
    return RecipeList(
        items=[_recipe_read(recipe) for recipe in recipes],
        total=len(recipes),
        page=1,
        limit=len(recipes),
    )


@router.post("/recipes/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    """Favorite a recipe idempotently."""
    await _get_recipe(session, recipe_id)
    favorite = await session.scalar(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.recipe_id == recipe_id,
        )
    )
    if favorite is None:
        session.add(Favorite(user_id=user.id, recipe_id=recipe_id))
        await session.commit()


@router.delete("/recipes/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    """Remove a favorite idempotently after confirming the recipe exists."""
    await _get_recipe(session, recipe_id)
    await session.execute(
        delete(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.recipe_id == recipe_id,
        )
    )
    await session.commit()
