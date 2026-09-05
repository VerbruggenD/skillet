"""Application entry point exposing the public FastAPI API routers."""

from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.types import ExceptionHandler

from .core.config import settings as app_settings
from .core.rate_limit import limit_login_router, limiter
from .core.users import auth_backend, fastapi_users
from .routers import auth, export, favorites, images, recipes, settings, suggestions, tags, users

app = FastAPI(
    title="Skillet API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in app_settings.cors_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(ExceptionHandler, _rate_limit_exceeded_handler))


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Return the API health status used by deployment and monitoring checks."""
    return JSONResponse({"status": "ok"})


# include routers
app.include_router(auth.router)
app.include_router(
    limit_login_router(fastapi_users.get_auth_router(auth_backend)),
    prefix="/api/auth/cookie",
    tags=["auth"],
)
app.include_router(users.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(images.router)
app.include_router(settings.router)
app.include_router(favorites.router)
app.include_router(suggestions.router)
app.include_router(export.router)
