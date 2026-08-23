"""Database-backed instance settings helpers."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Setting

PUBLIC_REGISTRATION_ENABLED = "public_registration_enabled"


async def get_public_registration_enabled(session: AsyncSession) -> bool:
    """Return whether unauthenticated users may register on this instance."""
    setting = await session.scalar(
        select(Setting).where(Setting.key == PUBLIC_REGISTRATION_ENABLED)
    )
    if setting is None:
        return True
    return setting.value.lower() == "true"
