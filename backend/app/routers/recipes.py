"""Recipe lifecycle and image-attachment routes."""

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.config import settings
from ..core.db import get_db
from ..core.users import current_user, current_user_optional
from ..models import Image, Ingredient, Recipe, Step, User
from ..schemas.recipes import (
    ImageRead,
    IngredientInput,
    RecipeCreate,
    RecipeList,
    RecipeRead,
    RecipeUpdate,
    StepInput,
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

_IMAGE_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _recipe_options():
    """Return eager-loading options needed by every recipe response."""
    return (
        selectinload(Recipe.ingredients),
        selectinload(Recipe.steps),
        selectinload(Recipe.images),
    )


def _recipe_read(recipe: Recipe) -> RecipeRead:
    """Produce a stable, ordered API representation from an eagerly loaded recipe."""
    return RecipeRead.model_validate(
        {
            "id": recipe.id,
            "owner_id": recipe.owner_id,
            "title": recipe.title,
            "description": recipe.description,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "servings": recipe.servings,
            "source_url": recipe.source_url,
            "is_locked": recipe.is_locked,
            "created_at": recipe.created_at,
            "ingredients": list(recipe.ingredients),
            "steps": sorted(recipe.steps, key=lambda step: step.order),
            "images": list(recipe.images),
        }
    )


async def _get_recipe_or_404(session: AsyncSession, recipe_id: int) -> Recipe:
    """Fetch a recipe and its child collections or return the standard not-found response."""
    statement = select(Recipe).where(Recipe.id == recipe_id).options(*_recipe_options())
    recipe = await session.scalar(statement)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


def _require_recipe_editor(recipe: Recipe, user: User) -> None:
    """Require recipe ownership unless the caller is an administrator."""
    if recipe.owner_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recipe owner or administrator required"
        )


def _replace_ingredients(recipe: Recipe, ingredients: Sequence[IngredientInput]) -> None:
    """Replace a recipe's ingredient collection with the submitted collection."""
    recipe.ingredients = [
        Ingredient(name=item.name, quantity=item.quantity, unit=item.unit, notes=item.notes)
        for item in ingredients
    ]


def _replace_steps(recipe: Recipe, steps: Sequence[StepInput]) -> None:
    """Replace instructions, deriving persisted order from their list position."""
    recipe.steps = [
        Step(order=index, instruction=item.instruction) for index, item in enumerate(steps, start=1)
    ]


@router.get("", response_model=RecipeList)
async def list_recipes(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RecipeList:
    """List recipes, hiding locked recipes only from anonymous visitors."""
    filters = [] if user is not None else [Recipe.is_locked.is_(False)]
    total = await session.scalar(select(func.count()).select_from(Recipe).where(*filters))
    statement = (
        select(Recipe)
        .where(*filters)
        .options(*_recipe_options())
        .order_by(Recipe.created_at.desc(), Recipe.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    recipes = (await session.scalars(statement)).unique().all()
    return RecipeList(
        items=[_recipe_read(recipe) for recipe in recipes], total=total or 0, page=page, limit=limit
    )


@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user_optional)],
) -> RecipeRead:
    """Retrieve one recipe, treating anonymous access to locked recipes as not found."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    if recipe.is_locked and user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return _recipe_read(recipe)


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    payload: RecipeCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeRead:
    """Create a recipe owned by the caller using their personal lock default."""
    recipe = Recipe(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        prep_time=payload.prep_time,
        cook_time=payload.cook_time,
        servings=payload.servings,
        source_url=str(payload.source_url) if payload.source_url else None,
        is_locked=user.default_recipe_locked,
    )
    _replace_ingredients(recipe, payload.ingredients)
    _replace_steps(recipe, payload.steps)
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe, attribute_names=["ingredients", "steps", "images"])
    return _recipe_read(recipe)


@router.patch("/{recipe_id}", response_model=RecipeRead)
async def update_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeRead:
    """Update a recipe partially when the caller owns it or administers the instance."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_recipe_editor(recipe, user)
    values = payload.model_dump(exclude_unset=True, exclude={"ingredients", "steps", "source_url"})
    for field, value in values.items():
        setattr(recipe, field, value)
    if "source_url" in payload.model_fields_set:
        recipe.source_url = str(payload.source_url) if payload.source_url else None
    if "ingredients" in payload.model_fields_set:
        _replace_ingredients(recipe, payload.ingredients or [])
    if "steps" in payload.model_fields_set:
        _replace_steps(recipe, payload.steps or [])
    await session.commit()
    await session.refresh(recipe, attribute_names=["ingredients", "steps", "images"])
    return _recipe_read(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    """Delete a recipe and its stored images when the caller may edit that recipe."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_recipe_editor(recipe, user)
    filenames = [image.filename for image in recipe.images]
    await session.delete(recipe)
    await session.commit()
    for filename in filenames:
        await asyncio.to_thread((Path(settings.upload_dir) / filename).unlink, missing_ok=True)


@router.post("/{recipe_id}/image", response_model=ImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    recipe_id: int,
    file: UploadFile | None,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> ImageRead:
    """Store a validated image attachment when the caller may edit the recipe."""
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")
    extension = _IMAGE_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported image type"
        )
    content = await file.read(settings.max_upload_size + 1)
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large"
        )
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_recipe_editor(recipe, user)
    filename = f"{uuid4()}{extension}"
    upload_path = Path(settings.upload_dir)
    await asyncio.to_thread(upload_path.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread((upload_path / filename).write_bytes, content)
    image = Image(recipe_id=recipe.id, filename=filename)
    session.add(image)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        await asyncio.to_thread((upload_path / filename).unlink, missing_ok=True)
        raise
    await session.refresh(image)
    return ImageRead.model_validate(image)


@router.delete("/{recipe_id}/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    recipe_id: int,
    image_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    """Delete one image attachment when the caller may edit its recipe."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_recipe_editor(recipe, user)
    image = next((item for item in recipe.images if item.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    filename = image.filename
    await session.delete(image)
    await session.commit()
    await asyncio.to_thread((Path(settings.upload_dir) / filename).unlink, missing_ok=True)
