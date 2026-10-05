"""
Smoke tests for ComicCraft.

These tests monkeypatch the AI-calling functions (Gemini text generation
and Stable Diffusion image generation) with instant fakes, so the whole
suite runs in a couple of seconds with no API key, no GPU, and no
internet connection required. What they DO verify for real:

  - the FastAPI app boots and all routes are wired up correctly
  - form data and JSON payloads are parsed and passed through correctly
  - generate_outline's output flows into generate_story, into
    build_comic_layout, into save_pdf without shape mismatches
  - a real PDF is produced by exporters.py (using the Helvetica fallback
    font, since the optional DejaVu TTF isn't bundled)

Run with (from the project root):
    pytest
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.routes as routes
from app.main import app

FAKE_OUTLINE = [
    {
        "panel": i,
        "title": f"Panel {i} Title",
        "scene_description": f"Scene description for panel {i}.",
        "image_prompt": f"A test illustration prompt for panel {i}.",
    }
    for i in range(1, 6)
]

FAKE_STORY = "\n\n".join(
    f"**Panel {i}: Panel {i} Title**\n"
    f"**CAPTION:** Ambient caption {i}.\n"
    f"**NARRATION:** Something happens in panel {i}.\n"
    f"**IMAGE PROMPT:** A test illustration prompt for panel {i}."
    for i in range(1, 6)
)


@pytest.fixture(autouse=True)
def patch_ai_calls(monkeypatch):
    """Replace slow/external AI calls with instant fakes for every test."""
    monkeypatch.setattr(routes, "generate_outline", lambda prompt: FAKE_OUTLINE)
    monkeypatch.setattr(routes, "generate_story", lambda outline: FAKE_STORY)

    def fake_generate_image(prompt, filename=None):
        # Write a tiny, valid placeholder PNG instead of running Stable
        # Diffusion, so exporters.py can still embed a real image in the PDF.
        path = Path("static/panels/test_panel.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), color=(120, 160, 200)).save(path)
        return str(path)

    monkeypatch.setattr(routes, "generate_image", fake_generate_image)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Create Your Comic" in response.text


def test_generate_comic_via_form(client):
    response = client.post("/generate", data={
        "prompt": "A brave fox explores an enchanted forest.",
        "character_name": "Free",
        "setting": "forest",
        "tone": "dramatic",
        "style": "realistic",
    })
    assert response.status_code == 200
    assert "Your Comic Preview" in response.text
    assert "Panel 1" in response.text
    assert "Panel 5" in response.text


def test_generate_comic_via_json(client):
    response = client.post("/generate-comic/json", json={
        "prompt": "A brave fox explores an enchanted forest.",
        "character_name": "Free",
        "setting": "forest",
        "tone": "dramatic",
        "style": "realistic",
    })
    assert response.status_code == 200

    data = response.json()
    assert len(data["layout"]) == 5
    assert data["layout"][0]["title"] == "Panel 1 Title"
    assert data["pdf_path"].startswith("/static/exports/")

    # The PDF referenced in the response should actually exist on disk.
    pdf_disk_path = Path(data["pdf_path"].lstrip("/"))
    assert pdf_disk_path.exists()
    assert pdf_disk_path.stat().st_size > 0


def test_json_route_uses_defaults_when_optional_fields_omitted(client):
    response = client.post("/generate-comic/json", json={
        "prompt": "A robot learns to paint.",
    })
    assert response.status_code == 200
    assert len(response.json()["layout"]) == 5


def test_test_image_route(client):
    response = client.get("/test-image", params={"prompt": "a cat astronaut"})
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Image generated successfully"
    assert Path(body["path"]).exists()


def test_export_success_page(client):
    response = client.get(
        "/export-success", params={"pdf_path": "/static/exports/example.pdf"}
    )
    assert response.status_code == 200
    assert "Comic Exported Successfully" in response.text
