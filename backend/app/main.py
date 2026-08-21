from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routers import auth, recipes, tags, images

app = FastAPI(title="Skillet API", openapi_url="/api/openapi.json", docs_url="/api/docs")


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


# include routers
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(images.router)
