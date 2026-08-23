"""Administrator-only instance settings routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import require_admin
from ..core.settings import PUBLIC_REGISTRATION_ENABLED, get_public_registration_enabled
from ..models import Setting, User
from ..schemas.settings import SettingsRead, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
async def read_settings(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SettingsRead:
    """Return the instance-wide settings visible to administrators."""
    return SettingsRead(
        public_registration_enabled=await get_public_registration_enabled(session),
    )


@router.patch("", response_model=SettingsRead)
async def update_settings(
    update: SettingsUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SettingsRead:
    """Persist an administrator's partial update to instance settings."""
    if update.public_registration_enabled is not None:
        setting = await session.scalar(
            select(Setting).where(Setting.key == PUBLIC_REGISTRATION_ENABLED)
        )
        value = str(update.public_registration_enabled).lower()
        if setting is None:
            session.add(Setting(key=PUBLIC_REGISTRATION_ENABLED, value=value))
        else:
            setting.value = value
        await session.commit()

    return SettingsRead(
        public_registration_enabled=await get_public_registration_enabled(session),
    )
