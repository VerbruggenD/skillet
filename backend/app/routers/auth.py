"""Authentication routes for login, logout, and current-user lookup."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login() -> JSONResponse:
    """Authenticate a user and return the session token once the auth flow is implemented."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented: login"})


@router.post("/logout")
async def logout() -> JSONResponse:
    """Invalidate the current user session and clear any auth cookies."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented: logout"})


@router.get("/me")
async def me() -> JSONResponse:
    """Return the currently authenticated user profile information."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented: me"})
