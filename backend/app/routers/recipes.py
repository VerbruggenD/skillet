from typing import Any
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get('/')
async def list_recipes(q: str | None = None):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: list recipes"})


@router.get('/{recipe_id}')
async def get_recipe(recipe_id: int):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: get recipe"})


@router.post('/')
async def create_recipe(payload: Any):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: create recipe"})


@router.put('/{recipe_id}')
async def update_recipe(recipe_id: int, payload: Any):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: update recipe"})


@router.delete('/{recipe_id}')
async def delete_recipe(recipe_id: int):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: delete recipe"})


@router.post('/{recipe_id}/image')
async def upload_image(recipe_id: int, file: UploadFile = File(...)):
    return JSONResponse(status_code=501, content={"detail": "Not implemented: upload image"})
