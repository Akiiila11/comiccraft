"""
Compiles a finished comic layout into a downloadable, multi-page PDF.
"""

import os
from datetime import datetime

from fpdf import FPDF

from app.config import FONT_PATH


def _to_latin1(text: str) -> str:
    """Fallback encoding for when a Unicode-capable font isn't available."""
    return text.encode("latin-1", "replace").decode("latin-1")


def save_pdf(layout: list) -> str:
    """
    Compiles the full comic into a multi-page PDF file using FPDF.
    Each panel's image and narration are placed on their own page.

    Args:
        layout (list): The structured comic layout from build_comic_layout().

    Returns:
        str: The relative path (e.g. "static/exports/comic_20260927_101500.pdf")
             to the saved PDF file.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Use a bundled Unicode font if available (recommended: DejaVu Sans,
    # see static/fonts/README.md), otherwise fall back to a built-in core
    # font and transliterate text to Latin-1 so the export never crashes.
    use_unicode_font = os.path.exists(FONT_PATH)
    if use_unicode_font:
        pdf.add_font("DejaVu", "", str(FONT_PATH))
        font_name = "DejaVu"
    else:
        font_name = "Helvetica"

    pdf.set_font(font_name, "", 12)

    for panel in layout:
        image_path = panel["image_path"]
        story_text = panel.get("text", "").strip()
        title_text = f"Panel {panel['panel']}: {panel.get('title', '')}"

        if not use_unicode_font:
            story_text = _to_latin1(story_text)
            title_text = _to_latin1(title_text)

        pdf.add_page()

        # Panel title
        pdf.set_font(font_name, "", 14)
        pdf.cell(0, 10, title_text, ln=True, align="C")
        pdf.set_font(font_name, "", 12)

        # Image placement
        y_image = 30
        image_height = 100
        spacing_after_image = 15

        if os.path.exists(image_path):
            pdf.image(image_path, x=10, y=y_image, w=pdf.w - 20, h=image_height)
        else:
            pdf.set_y(y_image)
            pdf.multi_cell(0, 10, f"Image missing: {image_path}")

        # Text placement below image
        pdf.set_y(y_image + image_height + spacing_after_image)
        pdf.multi_cell(0, 10, story_text)

    # Save with a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    pdf_path = os.path.join("static", "exports", filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.output(pdf_path)

    return pdf_path
