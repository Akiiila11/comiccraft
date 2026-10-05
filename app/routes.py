"""
All FastAPI routes for ComicCraft: the homepage form, the comic
generation pipeline (form-based and JSON-based), the export success
page, and a small developer utility for testing image generation alone.
"""

import traceback

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class PromptRequest(BaseModel):
    """JSON body accepted by /generate-comic/json."""
    prompt: str = Field(..., description="Main story idea for the comic.")
    character_name: str = Field("Hero", description="Name of the main character.")
    setting: str = Field("forest", description="Where the story takes place.")
    tone: str = Field("dramatic", description="Overall mood of the story.")
    style: str = Field("anime", description="Visual art style for the illustrations.")


def _build_full_prompt(prompt: str, character_name: str, setting: str, tone: str, style: str) -> str:
    return (
        f"{prompt}\n"
        f"The main character is {character_name}. "
        f"The setting is a {setting}. "
        f"The tone is {tone}. The art style is {style}."
    )


def _run_comic_pipeline(full_prompt: str) -> dict:
    """
    Shared end-to-end pipeline used by both the HTML form route and the
    JSON API route: outline -> story -> images -> layout -> PDF.
    """
    # Step 1: Generate panel outline
    outline = generate_outline(full_prompt)

    if not isinstance(outline, list) or not all(
        isinstance(panel, dict) and "image_prompt" in panel for panel in outline
    ):
        raise ValueError("Invalid outline structure from Gemini response.")

    # Step 2: Generate story
    full_story = generate_story(outline)

    # Step 3: Generate images
    # images = [generate_image(panel["image_prompt"]) for panel in outline]
    images = [
        generate_image(
            panel["image_prompt"],
            panel_number=index,
        )
        for index, panel in enumerate(outline, start=1)
    ]

    # Step 4: Build layout
    layout = build_comic_layout(images, full_story, outline)

    # Step 5: Export to PDF
    pdf_path = save_pdf(layout)
    web_pdf_path = "/" + pdf_path.replace("\\", "/")  # Make path safe for web

    return {"layout": layout, "pdf_path": web_pdf_path}


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Loads the homepage where users submit their story details."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...),
):
    """Handles the homepage form submission and renders the comic preview."""
    try:
        full_prompt = _build_full_prompt(prompt, character_name, setting, tone, style)
        result = _run_comic_pipeline(full_prompt)

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": result["layout"],
                "pdf_path": result["pdf_path"],
            }
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    """Same pipeline as /generate, but for JSON API clients."""
    try:
        full_prompt = _build_full_prompt(
            payload.prompt, payload.character_name, payload.setting, payload.tone, payload.style
        )
        result = _run_comic_pipeline(full_prompt)

        return JSONResponse({
            "layout": result["layout"],
            "pdf_path": result["pdf_path"],
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: str):
    """Displays a success confirmation page after the comic is downloaded."""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path,
        }
    )


@router.get("/test-image")
async def test_image(prompt: str = "A futuristic city at sunset, sci-fi, cinematic, artstation"):
    """Developer utility: test image generation directly, without a full comic."""
    try:
        image_path = generate_image(prompt)
        return {"message": "Image generated successfully", "path": image_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
