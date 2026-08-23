"""Schemas for the instance settings API."""

from pydantic import BaseModel


class SettingsRead(BaseModel):
    """The instance settings currently exposed to administrators."""

    public_registration_enabled: bool


class SettingsUpdate(BaseModel):
    """A partial update to the editable instance settings."""

    public_registration_enabled: bool | None = None
