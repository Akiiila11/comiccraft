"""
ComicCraft - AI Comic Story Creator
Application entrypoint. Run with:

    uvicorn app.main:app --reload

from the project root (the folder that contains this "app" package).
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

app = FastAPI(
    title="ComicCraft",
    description="AI Comic Story Creator using Gemini models and Stable Diffusion.",
    version="1.0.0",
)

# Serves everything under static/ (generated panel images and PDFs) at /static/...
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)
