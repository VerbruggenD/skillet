"""Application entry point exposing the public FastAPI API routers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routers import auth, images, recipes, tags

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
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(images.router)
