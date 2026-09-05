"""Tag listing routes used for recipe categorization and search."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import require_admin
from ..models import Tag, User
from ..schemas.recipes import TagRead

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(session: Annotated[AsyncSession, Depends(get_db)]) -> list[Tag]:
    """Return all available recipe tags for browse filters."""
    return list((await session.scalars(select(Tag).order_by(Tag.name.asc()))).all())


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a tag and its recipe associations as an administrator."""
    tag = await session.scalar(select(Tag).where(Tag.id == tag_id))
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await session.delete(tag)
    await session.commit()
