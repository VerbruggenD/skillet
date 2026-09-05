"""Request and response schemas for recipe lifecycle endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class IngredientInput(BaseModel):
    """A single ingredient supplied as part of a recipe write."""

    name: str = Field(min_length=1, max_length=255)
    quantity: float | None = None
    unit: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class TagRead(BaseModel):
    """Recipe tag metadata returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class StepInput(BaseModel):
    """A single ordered preparation instruction supplied in a recipe write."""

    instruction: str = Field(min_length=1)


class RecipeCreate(BaseModel):
    """Fields accepted when a signed-in user creates a recipe."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    prep_time: int | None = Field(default=None, ge=0)
    cook_time: int | None = Field(default=None, ge=0)
    servings: int | None = Field(default=None, ge=1)
    source_url: HttpUrl | None = None
    ingredients: list[IngredientInput] = Field(default_factory=list)
    steps: list[StepInput] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list, max_length=50)


class RecipeUpdate(BaseModel):
    """Partial recipe update; supplied ingredient and step lists replace their current lists."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    prep_time: int | None = Field(default=None, ge=0)
    cook_time: int | None = Field(default=None, ge=0)
    servings: int | None = Field(default=None, ge=1)
    source_url: HttpUrl | None = None
    is_locked: bool | None = None
    ingredients: list[IngredientInput] | None = None
    steps: list[StepInput] | None = None
    tags: list[str] | None = Field(default=None, max_length=50)


class IngredientRead(IngredientInput):
    """Ingredient data returned with a recipe."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class StepRead(StepInput):
    """Instruction data returned with a recipe."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order: int


class ImageRead(BaseModel):
    """Stored recipe-image metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    created_at: datetime


class RecipeRead(BaseModel):
    """Complete recipe representation returned by lifecycle endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None
    title: str
    description: str | None
    prep_time: int | None
    cook_time: int | None
    servings: int | None
    source_url: str | None
    is_locked: bool
    created_at: datetime
    ingredients: list[IngredientRead]
    steps: list[StepRead]
    images: list[ImageRead]
    tags: list[TagRead]


class RecipeList(BaseModel):
    """Paginated recipe search result."""

    items: list[RecipeRead]
    total: int
    page: int
    limit: int
