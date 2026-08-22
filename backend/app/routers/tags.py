from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/")
async def list_tags():
    return JSONResponse(
        status_code=501, content={"detail": "Not implemented: list tags"}
    )
