"""Request and response schemas for recipe suggestions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .recipes import RecipeUpdate


class SuggestionCreate(BaseModel):
    """A complete proposed recipe update submitted for owner review."""

    payload: RecipeUpdate
    note: str | None = Field(default=None, max_length=2000)


class SuggestionRead(BaseModel):
    """A recipe suggestion and its review state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    suggested_by: int
    payload: dict[str, Any]
    note: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: int | None
