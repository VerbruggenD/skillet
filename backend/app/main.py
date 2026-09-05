"""Application entry point exposing the public FastAPI API routers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .core.users import auth_backend, fastapi_users
from .routers import auth, favorites, images, recipes, settings, suggestions, tags, users

app = FastAPI(
    title="Skillet API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Return the API health status used by deployment and monitoring checks."""
    return JSONResponse({"status": "ok"})


# include routers
app.include_router(auth.router)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
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
