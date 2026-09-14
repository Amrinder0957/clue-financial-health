from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="CLUE API",
    description="Financial health check-up API for small businesses",
    version="1.0.0",
)

app.include_router(router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")