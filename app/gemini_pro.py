# """
# Gemini Pro integration: expands a panel outline into full comic narration
# and character dialogue.
# """

# from google import genai

# from app.config import GEMINI_API_KEY, GEMINI_PRO_MODEL

# _client = None


# def _get_client() -> genai.Client:
#     """Lazily creates a single shared Gemini client for this process."""
#     global _client
#     if _client is None:
#         if not GEMINI_API_KEY:
#             raise RuntimeError(
#                 "GEMINI_API_KEY is not set. Add it to your .env file "
#                 "(see .env.example)."
#             )
#         _client = genai.Client(api_key=GEMINI_API_KEY)
#     return _client


# def generate_story(outline: list) -> str:
#     """
#     Generates a detailed comic story with narration and character dialogue
#     from a list of comic panel outlines using Gemini Pro.

#     Args:
#         outline (list): A list of panel dictionaries from generate_outline()
#                          (each with "panel", "title", "scene_description",
#                          "image_prompt").

#     Returns:
#         str: The generated comic story text (one "**Panel N: Title**" block
#              per panel, so build_comic_layout() can split it back apart), or
#              an error message string.
#     """
#     # Format the panel outline as a numbered list for clarity
#     formatted_outline = "\n".join(
#         f"Panel {panel.get('panel', i + 1)}: {panel.get('title', '')}\n"
#         f"  Scene: {panel.get('scene_description', '')}\n"
#         f"  Visual idea: {panel.get('image_prompt', '')}"
#         for i, panel in enumerate(outline)
#     )

#     prompt = f"""
# You're a comic book writer.

# Given the following panel breakdown, write a comic-style story with engaging narration and character dialogues for each panel.

# Panel Outline:
# {formatted_outline}

# Write your response using EXACTLY this structure, repeated once per panel, with
# nothing else before or after it:

# **Panel <number>: <panel title>**
# **CAPTION:** <a short, ambient description of the environment or background sounds>
# **NARRATION:** <the main character's actions, emotions, or dialogue in this scene>
# **IMAGE PROMPT:** <a vivid artistic description suitable for an image-generation model>

# Guidelines:
# - Use a fun and engaging tone, like an actual comic book.
# - Include narration and clearly marked character lines.
# - Keep each panel self-contained but part of a cohesive story.
# - Do not repeat the scene description verbatim; focus on caption, narration, and image prompt.
# """

#     try:
#         client = _get_client()
#         response = client.models.generate_content(
#             model=GEMINI_PRO_MODEL,
#             contents=prompt,
#         )
#         return response.text
#     except Exception as e:
#         return f"Error generating story: {str(e)}"


"""
Gemini Pro integration: expands a panel outline into full comic narration
and character dialogue.
"""

import time

from google import genai

from app.config import GEMINI_API_KEY, GEMINI_PRO_MODEL


_client = None


def _get_client() -> genai.Client:
    """Lazily creates a single shared Gemini client for this process."""
    global _client

    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file "
                "(see .env.example)."
            )

        _client = genai.Client(api_key=GEMINI_API_KEY)

    return _client


def generate_story(outline: list) -> str:
    """
    Generates the readable comic story from the panel outline.

    Gemini Pro is responsible only for:
    - captions
    - narration
    - character dialogue

    Image prompts are intentionally NOT generated here because
    Gemini Flash already creates the prompts used by Stable Diffusion.
    """

    formatted_outline = "\n".join(
        f"Panel {panel.get('panel', i + 1)}: {panel.get('title', '')}\n"
        f"Scene: {panel.get('scene_description', '')}"
        for i, panel in enumerate(outline)
    )

    prompt = f"""
You are a professional comic book writer.

Create the readable story for a 5-panel comic from the panel outline below.

PANEL OUTLINE:

{formatted_outline}

IMPORTANT:

The story must follow the exact order of the five panels.

The same main character must remain consistent throughout the story.

For every panel, write:

**Panel <number>: <panel title>**

**CAPTION:** A short description of the environment, atmosphere,
background sounds, or location.

**NARRATION:** Describe what the character does, thinks, feels,
or says. Include natural character dialogue when appropriate.

Do NOT create an IMAGE PROMPT.

Do NOT include visual-generation instructions.

Do NOT include technical descriptions for Stable Diffusion.

Do NOT include anything before Panel 1.

Do NOT include anything after Panel 5.

Keep the narration concise enough to fit comfortably below a comic image.

The five panels should form a continuous story:

Panel 1 → Setup
Panel 2 → Discovery / development
Panel 3 → Main event
Panel 4 → Action / interaction
Panel 5 → Resolution

Make character dialogue natural and relevant to what is happening.

Use exactly this format:

**Panel 1: Title**

**CAPTION:** Short environment or atmosphere description.

**NARRATION:** Character action, emotion, thoughts, and/or dialogue.

**Panel 2: Title**

**CAPTION:** Short environment or atmosphere description.

**NARRATION:** Character action, emotion, thoughts, and/or dialogue.

Repeat the same structure through Panel 5.

Return ONLY the five panel blocks.
"""

    client = _get_client()

    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(
                f"\n✍️ Generating comic story "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            response = client.models.generate_content(
                model=GEMINI_PRO_MODEL,
                contents=prompt,
            )

            story = (response.text or "").strip()

            if not story:
                raise ValueError("Gemini returned an empty story.")

            print("✅ Comic story generated successfully.")

            return story

        except Exception as e:
            error_text = str(e)

            print(
                f"\n❌ Gemini story attempt "
                f"{attempt + 1}/{max_retries} failed:"
            )
            print(error_text)

            if "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt

                    print(
                        f"⏳ Gemini temporarily unavailable. "
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)
                    continue

                raise RuntimeError(
                    "Gemini story generation is temporarily unavailable "
                    f"after {max_retries} attempts."
                ) from e

            raise RuntimeError(
                f"Gemini story generation failed: {error_text}"
            ) from e

    raise RuntimeError(
        "Gemini story generation failed after all retry attempts."
    )