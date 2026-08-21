from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post('/login')
async def login():
    return JSONResponse(status_code=501, content={"detail": "Not implemented: login"})


@router.post('/logout')
async def logout():
    return JSONResponse(status_code=501, content={"detail": "Not implemented: logout"})


@router.get('/me')
async def me():
    return JSONResponse(status_code=501, content={"detail": "Not implemented: me"})
