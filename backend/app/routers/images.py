"""Image upload routes for recipe assets."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/")
async def upload_image() -> JSONResponse:
    """Store a single uploaded image and return the created asset metadata."""
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: upload image"}
    )
