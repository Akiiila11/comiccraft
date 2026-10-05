# """
# Stable Diffusion integration: turns an image prompt from the comic outline
# into a saved illustration for that panel.

# The pipeline is loaded lazily on first use (not at import time), so the
# app still starts instantly and /docs works even before any model weights
# have been downloaded.
# """

# import os
# import re
# import uuid

# import torch
# from diffusers import StableDiffusionPipeline

# from app.config import SD_MODEL_ID, SD_DEVICE

# _pipe = None


# def _resolve_device() -> str:
#     if SD_DEVICE != "auto":
#         return SD_DEVICE
#     if torch.cuda.is_available():
#         return "cuda"
#     if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
#         return "mps"
#     return "cpu"


# def _get_pipeline() -> StableDiffusionPipeline:
#     global _pipe
#     if _pipe is None:
#         device = _resolve_device()
#         dtype = torch.float16 if device == "cuda" else torch.float32

#         print(
#             f"🎨 Loading Stable Diffusion pipeline '{SD_MODEL_ID}' on device "
#             f"'{device}' (first run downloads several GB and may take a while)..."
#         )

#         _pipe = StableDiffusionPipeline.from_pretrained(SD_MODEL_ID, torch_dtype=dtype)
#         _pipe = _pipe.to(device)

#         if device == "cpu":
#             # Keeps peak memory usage manageable on CPU-only machines.
#             _pipe.enable_attention_slicing()

#     return _pipe


# def sanitize_filename(prompt: str) -> str:
#     """Turns a free-form prompt into a safe, unique filename."""
#     slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt.strip().lower())[:40].strip("_")
#     unique = uuid.uuid4().hex[:8]
#     return f"{slug or 'panel'}_{unique}.png"


# def generate_image(prompt: str, filename: str = None) -> str:
#     """
#     Uses the Stable Diffusion model to create a comic-style image based on
#     the provided image prompt.

#     Args:
#         prompt (str): The image generation prompt.
#         filename (str, optional): Filename to save the image as. A safe,
#             unique one is generated from the prompt if omitted.

#     Returns:
#         str: The relative path to the saved image (e.g.
#              "static/panels/a_brave_fox_1a2b3c4d.png").
#     """
#     if not filename:
#         filename = sanitize_filename(prompt)

#     pipe = _get_pipeline()
#     image = pipe(prompt).images[0]

#     path = f"static/panels/{filename}"
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     image.save(path)
#     return path

"""
Stable Diffusion integration: turns an image prompt from the comic outline
into a saved illustration for that panel.

The pipeline is loaded lazily on first use.
"""

import os
import re
import uuid

import torch
from diffusers import StableDiffusionPipeline

from app.config import SD_MODEL_ID, SD_DEVICE


_pipe = None
_device = None


# Shared seed for visual consistency.
# Change this number if you want a different comic look.
BASE_SEED = 12345


# Negative prompt helps prevent unwanted image characteristics.
NEGATIVE_PROMPT = """
blurry,
low quality,
low resolution,
bad anatomy,
deformed body,
extra arms,
extra legs,
extra fingers,
missing fingers,
duplicate character,
multiple characters,
distorted face,
bad hands,
cropped character,
cut off body,
out of frame,
text,
letters,
words,
watermark,
logo,
signature,
photorealistic,
3d render,
disfigured,
ugly,
messy composition
"""


def _resolve_device() -> str:
    if SD_DEVICE != "auto":
        return SD_DEVICE

    if torch.cuda.is_available():
        return "cuda"

    if (
        getattr(torch.backends, "mps", None)
        and torch.backends.mps.is_available()
    ):
        return "mps"

    return "cpu"


def _get_pipeline() -> StableDiffusionPipeline:
    global _pipe
    global _device

    if _pipe is None:
        _device = _resolve_device()

        dtype = (
            torch.float16
            if _device == "cuda"
            else torch.float32
        )

        print(
            f"🎨 Loading Stable Diffusion pipeline "
            f"'{SD_MODEL_ID}' on device '{_device}'..."
        )

        _pipe = StableDiffusionPipeline.from_pretrained(
            SD_MODEL_ID,
            torch_dtype=dtype,
            safety_checker=None,
        )

        _pipe = _pipe.to(_device)

        # CUDA optimizations
        if _device == "cuda":
            try:
                _pipe.enable_attention_slicing()
            except Exception:
                pass

            try:
                _pipe.enable_vae_slicing()
            except Exception:
                pass

            # Faster matrix multiplication on supported NVIDIA GPUs.
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
            except Exception:
                pass

        # CPU memory optimization
        elif _device == "cpu":
            _pipe.enable_attention_slicing()

    return _pipe


def sanitize_filename(prompt: str) -> str:
    """Turns a free-form prompt into a safe, unique filename."""

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        prompt.strip().lower(),
    )[:40].strip("_")

    unique = uuid.uuid4().hex[:8]

    return f"{slug or 'panel'}_{unique}.png"


def generate_image(
    prompt: str,
    filename: str = None,
    panel_number: int = 1,
) -> str:
    """
    Generates a comic panel image.

    Args:
        prompt:
            Detailed visual prompt generated by Gemini Flash.

        filename:
            Optional output filename.

        panel_number:
            Panel number used to create a deterministic but different
            seed for each panel.

    Returns:
        Relative path to the generated image.
    """

    if not filename:
        filename = sanitize_filename(prompt)

    pipe = _get_pipeline()

    # Same base seed + different panel number.
    #
    # This keeps the generation deterministic while preventing
    # every panel from being generated from exactly the same noise.
    seed = BASE_SEED + panel_number

    generator = torch.Generator(
        device=_device
    ).manual_seed(seed)

    print(
        f"🖼️ Generating panel {panel_number} "
        f"with seed {seed}..."
    )

    image = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=40,
        guidance_scale=8.0,
        width=512,
        height=512,
        generator=generator,
    ).images[0]

    path = f"static/panels/{filename}"

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    image.save(path)

    print(
        f"✅ Panel {panel_number} saved: {path}"
    )

    return path