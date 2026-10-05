"""
Central configuration for ComicCraft.

Loads environment variables (from a .env file if present) and exposes
shared constants used across the AI integration, routing, and export
modules. Keeping this in one place means every module reads the same
settings and the project folders always exist before they're used.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a .env file in the project root, if one exists.
load_dotenv()

# Project root = the folder that contains the "app" package.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Model selection
#
# NOTE: Gemini 1.5 Flash/Pro (the models named in the original project
# spec) have been fully retired by Google and no longer respond to API
# calls. "gemini-flash-latest" / "gemini-pro-latest" are Google's rolling
# aliases that always point at the current recommended model, so this
# code keeps working as Google upgrades its lineup. Pin an exact model
# name here (or in .env) if you want reproducible behavior instead.
# ---------------------------------------------------------------------------
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-flash-latest")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-pro-latest")

# Stable Diffusion checkpoint used for panel illustrations.
# "runwayml/stable-diffusion-v1-5" (named in the original spec) was taken
# down from Hugging Face; this is the actively maintained mirror.
SD_MODEL_ID = os.getenv("SD_MODEL_ID", "stable-diffusion-v1-5/stable-diffusion-v1-5")

# "auto" picks CUDA > Apple MPS > CPU. Override with "cuda", "mps", or "cpu".
SD_DEVICE = os.getenv("SD_DEVICE", "auto")

# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------
PANELS_DIR = BASE_DIR / "static" / "panels"
EXPORTS_DIR = BASE_DIR / "static" / "exports"
FONTS_DIR = BASE_DIR / "static" / "fonts"

# Optional Unicode TTF font for PDF export (see static/fonts/README.md).
# If it isn't present, exporters.py falls back to a built-in core font.
FONT_PATH = FONTS_DIR / "DejaVuSans.ttf"

# Make sure the runtime folders exist so the app never crashes on a
# fresh checkout just because a directory is missing.
for _dir in (PANELS_DIR, EXPORTS_DIR, FONTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
