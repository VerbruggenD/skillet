"""SQLAlchemy models describing the core Skillet domain entities."""

from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTable
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative model used across the application schema."""


class User(SQLAlchemyBaseUserTable[int], Base):
    """Application user account and authentication state."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    default_recipe_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    access_tokens: Mapped[list["AccessToken"]] = relationship(back_populates="user")


class AccessToken(SQLAlchemyBaseAccessTokenTable[int], Base):
    """API access token issued to an authenticated user."""

    __tablename__ = "access_tokens"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="access_tokens")


class Recipe(Base):
    """Recipe content, metadata, and ownership information."""

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    search_vector: Mapped[object | None] = mapped_column(TSVECTOR, nullable=True)

    owner: Mapped[User | None] = relationship()
    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="recipe")
    steps: Mapped[list["Step"]] = relationship(back_populates="recipe")
    images: Mapped[list["Image"]] = relationship(back_populates="recipe")


class Ingredient(Base):
    """Ingredient entry attached to a recipe."""

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")


class Step(Base):
    """Single instruction step in a recipe preparation flow."""

    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    recipe: Mapped[Recipe] = relationship(back_populates="steps")


class Tag(Base):
    """Reusable recipe tag metadata."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class RecipeTag(Base):
    """Many-to-many link between recipes and their tags."""

    __tablename__ = "recipe_tags"

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Image(Base):
    """Uploaded image asset attached to a recipe."""

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    recipe: Mapped[Recipe] = relationship(back_populates="images")


class Favorite(Base):
    """User favorite relationship for recipe shortlists."""

    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RecipeSuggestion(Base):
    """Suggestion payload submitted for a recipe review or moderation flow."""

    __tablename__ = "recipe_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    suggested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class Setting(Base):
    """Custom application setting stored as a key/value pair."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
