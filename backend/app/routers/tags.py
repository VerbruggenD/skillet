"""Tag listing routes used for recipe categorization and search."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/")
async def list_tags() -> JSONResponse:
    """Return the available recipe tags for the UI and search filters."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented: list tags"})
