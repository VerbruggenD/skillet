"""Recipe suggestion submission and review routes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.users import current_user
from ..models import Recipe, RecipeSuggestion, User
from ..schemas.recipes import RecipeUpdate
from ..schemas.suggestions import SuggestionCreate, SuggestionRead
from .recipes import _get_recipe_or_404, _replace_ingredients, _replace_steps

router = APIRouter(prefix="/api", tags=["suggestions"])


def _require_reviewer(recipe: Recipe, user: User) -> None:
    """Require the recipe owner or an administrator to review suggestions."""
    if recipe.owner_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recipe owner or administrator required",
        )


def _require_pending(suggestion: RecipeSuggestion) -> None:
    """Reject review actions once a suggestion has been resolved or withdrawn."""
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Suggestion is no longer pending",
        )


async def _get_suggestion(
    session: AsyncSession, recipe_id: int, suggestion_id: int
) -> RecipeSuggestion:
    """Fetch a suggestion belonging to the requested recipe."""
    suggestion = await session.scalar(
        select(RecipeSuggestion).where(
            RecipeSuggestion.id == suggestion_id,
            RecipeSuggestion.recipe_id == recipe_id,
        )
    )
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    return suggestion


async def _apply_payload(recipe: Recipe, payload: RecipeUpdate, session: AsyncSession) -> None:
    """Apply a validated suggestion payload using normal recipe update semantics."""
    values = payload.model_dump(exclude_unset=True, exclude={"ingredients", "steps", "source_url"})
    for field, value in values.items():
        setattr(recipe, field, value)
    if "source_url" in payload.model_fields_set:
        recipe.source_url = str(payload.source_url) if payload.source_url else None
    if "ingredients" in payload.model_fields_set:
        _replace_ingredients(recipe, payload.ingredients or [])
    if "steps" in payload.model_fields_set:
        await _replace_steps(recipe, payload.steps or [], session)


@router.post(
    "/recipes/{recipe_id}/suggestions",
    response_model=SuggestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_suggestion(
    recipe_id: int,
    payload: SuggestionCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeSuggestion:
    """Submit a complete proposed recipe replacement for owner review."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    if recipe.owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners must edit their own recipes directly",
        )
    suggestion = RecipeSuggestion(
        recipe_id=recipe.id,
        suggested_by=user.id,
        payload=payload.payload.model_dump(mode="json", exclude_unset=True),
        note=payload.note,
        status="pending",
    )
    session.add(suggestion)
    await session.commit()
    await session.refresh(suggestion)
    return suggestion


@router.get("/recipes/{recipe_id}/suggestions", response_model=list[SuggestionRead])
async def list_recipe_suggestions(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> list[RecipeSuggestion]:
    """List a recipe's suggestion queue for its owner or an administrator."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_reviewer(recipe, user)
    result = await session.scalars(
        select(RecipeSuggestion)
        .where(RecipeSuggestion.recipe_id == recipe_id)
        .order_by(RecipeSuggestion.created_at.asc(), RecipeSuggestion.id.asc())
    )
    return list(result.all())


@router.get("/suggestions/mine", response_model=list[SuggestionRead])
async def list_my_suggestions(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> list[RecipeSuggestion]:
    """List suggestions submitted by the current user."""
    result = await session.scalars(
        select(RecipeSuggestion)
        .where(RecipeSuggestion.suggested_by == user.id)
        .order_by(RecipeSuggestion.created_at.desc(), RecipeSuggestion.id.desc())
    )
    return list(result.all())


@router.post(
    "/recipes/{recipe_id}/suggestions/{suggestion_id}/accept",
    response_model=SuggestionRead,
)
async def accept_suggestion(
    recipe_id: int,
    suggestion_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeSuggestion:
    """Apply a pending suggestion and mark it accepted."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_reviewer(recipe, user)
    suggestion = await _get_suggestion(session, recipe_id, suggestion_id)
    _require_pending(suggestion)
    await _apply_payload(recipe, RecipeUpdate.model_validate(suggestion.payload), session)
    suggestion.status = "accepted"
    suggestion.resolved_at = datetime.now(timezone.utc)
    suggestion.resolved_by = user.id
    await session.commit()
    await session.refresh(suggestion)
    return suggestion


@router.post(
    "/recipes/{recipe_id}/suggestions/{suggestion_id}/reject",
    response_model=SuggestionRead,
)
async def reject_suggestion(
    recipe_id: int,
    suggestion_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> RecipeSuggestion:
    """Reject a pending suggestion without changing the recipe."""
    recipe = await _get_recipe_or_404(session, recipe_id)
    _require_reviewer(recipe, user)
    suggestion = await _get_suggestion(session, recipe_id, suggestion_id)
    _require_pending(suggestion)
    suggestion.status = "rejected"
    suggestion.resolved_at = datetime.now(timezone.utc)
    suggestion.resolved_by = user.id
    await session.commit()
    await session.refresh(suggestion)
    return suggestion


@router.delete(
    "/recipes/{recipe_id}/suggestions/{suggestion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def withdraw_suggestion(
    recipe_id: int,
    suggestion_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    """Withdraw a pending suggestion as its author or delete it as an admin."""
    suggestion = await _get_suggestion(session, recipe_id, suggestion_id)
    if user.is_superuser:
        await session.delete(suggestion)
    elif suggestion.suggested_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Suggestion author required"
        )
    else:
        _require_pending(suggestion)
        suggestion.status = "withdrawn"
        suggestion.resolved_at = datetime.now(timezone.utc)
        suggestion.resolved_by = user.id
    await session.commit()
