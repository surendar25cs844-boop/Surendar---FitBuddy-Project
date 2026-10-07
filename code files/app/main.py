from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import Base, engine
from app.routes import router


BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FitBuddy",
    description="Personalized fitness plans and wellness tips",
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.include_router(router)