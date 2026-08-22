"""Recipe CRUD and media routes for the Skillet API."""

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("/")
async def list_recipes(q: str | None = None) -> JSONResponse:
    """List recipes with optional search text.

    Placeholder behavior remains until the query layer is implemented.
    """
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: list recipes"}
    )


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: int) -> JSONResponse:
    """Retrieve a single recipe by its numeric identifier."""
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: get recipe"}
    )


@router.post("/")
async def create_recipe(payload: Any) -> JSONResponse:
    """Create a recipe from the submitted payload when the recipe service is implemented."""
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: create recipe"}
    )


@router.put("/{recipe_id}")
async def update_recipe(recipe_id: int, payload: Any) -> JSONResponse:
    """Update an existing recipe with the provided patch or replacement payload."""
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: update recipe"}
    )


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int) -> JSONResponse:
    """Delete a recipe identified by the given recipe identifier."""
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: delete recipe"}
    )


@router.post("/{recipe_id}/image")
async def upload_image(recipe_id: int, file: UploadFile | None = None) -> JSONResponse:
    """Upload a recipe image for the target recipe once storage is implemented."""
    if file is None:
        raise HTTPException(status_code=400, detail="File is required")
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: upload image"}
    )
