# """
# Gemini Flash integration: turns a user's story idea into a structured,
# 5-panel comic outline.
# """

# import json
# import time

# from google import genai

# from app.config import GEMINI_API_KEY, GEMINI_FLASH_MODEL

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


# def generate_outline(user_prompt: str) -> list:
#     """
#     Generates a 5-panel comic layout based on the user's story idea using Gemini.

#     Returns:
#         list: A list containing exactly 5 panel dictionaries.
#     """

#     prompt = f"""
# You are a professional AI comic planner.

# Your task is to generate a strictly formatted JSON array containing
# exactly 5 panel descriptions for a comic based on the story idea below.

# STORY: "{user_prompt}"

# Each JSON object must include:
# - "panel" (integer)
# - "title" (string)
# - "scene_description" (string)
# - "image_prompt" (string)

# Respond ONLY with valid JSON.
# Do not include explanations.
# Do not use markdown code fences.

# Expected format:

# [
#   {{
#     "panel": 1,
#     "title": "Title here",
#     "scene_description": "Scene description here",
#     "image_prompt": "Image prompt for Stable Diffusion"
#   }},
#   {{
#     "panel": 2,
#     "title": "Title here",
#     "scene_description": "Scene description here",
#     "image_prompt": "Image prompt for Stable Diffusion"
#   }}
# ]
# """

#     client = _get_client()

#     # Number of times we will try Gemini
#     max_retries = 3

#     for attempt in range(max_retries):

#         try:
#             print(
#                 f"\n🤖 Generating comic outline "
#                 f"(attempt {attempt + 1}/{max_retries})..."
#             )

#             response = client.models.generate_content(
#                 model=GEMINI_FLASH_MODEL,
#                 contents=prompt,
#             )

#             output_text = (response.text or "").strip()

#             print("\n🔵 RAW GEMINI RESPONSE 🔵")
#             print(output_text)

#             # Remove markdown code fences if Gemini adds them
#             if output_text.startswith("```json"):
#                 output_text = output_text[7:]

#                 if output_text.endswith("```"):
#                     output_text = output_text[:-3]

#                 output_text = output_text.strip()

#             elif output_text.startswith("```"):
#                 output_text = output_text[3:]

#                 if output_text.endswith("```"):
#                     output_text = output_text[:-3]

#                 output_text = output_text.strip()

#             # Convert Gemini JSON text into Python list
#             panel_data = json.loads(output_text)

#             # Make sure response is a list
#             if not isinstance(panel_data, list):
#                 raise ValueError(
#                     "Gemini response is not a JSON list."
#                 )

#             # ComicCraft requires exactly 5 panels
#             if len(panel_data) != 5:
#                 raise ValueError(
#                     f"Expected 5 panels, but Gemini returned "
#                     f"{len(panel_data)} panels."
#                 )

#             # Validate every panel
#             required_keys = (
#                 "panel",
#                 "title",
#                 "scene_description",
#                 "image_prompt",
#             )

#             for panel in panel_data:

#                 if not isinstance(panel, dict):
#                     raise ValueError(
#                         f"Invalid panel format: {panel}"
#                     )

#                 missing_keys = [
#                     key
#                     for key in required_keys
#                     if key not in panel
#                 ]

#                 if missing_keys:
#                     raise ValueError(
#                         f"Panel is missing required keys: "
#                         f"{missing_keys}"
#                     )

#             print("✅ Gemini outline generated successfully.")

#             return panel_data

#         except json.JSONDecodeError as e:

#             print("❌ JSON Decode Error:", e)

#             # Gemini responded, but the response was not valid JSON.
#             # Retrying usually isn't necessary.
#             raise RuntimeError(
#                 f"Gemini returned invalid JSON: {e}"
#             ) from e

#         except Exception as e:

#             error_text = str(e)

#             print(
#                 f"\n❌ Gemini attempt "
#                 f"{attempt + 1}/{max_retries} failed:"
#             )
#             print(error_text)

#             # Retry temporary Gemini availability errors
#             if "503" in error_text or "UNAVAILABLE" in error_text:

#                 if attempt < max_retries - 1:

#                     # 1 second → 2 seconds → 4 seconds
#                     delay = 2 ** attempt

#                     print(
#                         f"⏳ Gemini is temporarily unavailable."
#                     )
#                     print(
#                         f"🔄 Retrying in {delay} seconds..."
#                     )

#                     time.sleep(delay)

#                     continue

#                 # All retries exhausted
#                 raise RuntimeError(
#                     "Gemini is temporarily unavailable after "
#                     f"{max_retries} attempts. Please try again later."
#                 ) from e

#             # Other errors should immediately be reported
#             raise RuntimeError(
#                 f"Gemini outline generation failed: {error_text}"
#             ) from e

#     raise RuntimeError(
#         "Gemini outline generation failed after all retry attempts."
#     )

"""
Gemini Flash integration: turns a user's story idea into a structured,
5-panel comic outline optimized for consistent image generation.
"""

import json
import time

from google import genai

from app.config import GEMINI_API_KEY, GEMINI_FLASH_MODEL

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


def generate_outline(user_prompt: str) -> list:
    """
    Generates a 5-panel comic outline optimized for Stable Diffusion.

    Each panel contains:
    - panel
    - title
    - scene_description
    - image_prompt

    The image prompts explicitly describe:
    - the same main character
    - the character's appearance
    - the character's action
    - important objects
    - environment
    - camera composition
    - lighting
    """

    prompt = f"""
You are a professional comic storyboard artist and AI image-generation prompt
designer.

Create a complete 5-panel comic from the story idea below.

STORY:
"{user_prompt}"

IMPORTANT:
The five panels must feel like scenes from the SAME comic.
The main character must remain visually consistent across all five panels.

Before creating the panels, establish a FIXED visual identity for the main
character internally.

The character's:
- species/person identity
- age
- gender
- body type
- face
- hair/fur
- clothing
- clothing colors
- accessories
- distinctive features

must remain consistent across ALL panels.

Do not redesign the character between panels.

STORY STRUCTURE:

Panel 1:
Introduce the character and establish the environment.

Panel 2:
Show the character moving toward or discovering the important situation,
object, location, or conflict.

Panel 3:
Show the main event or discovery clearly.

Panel 4:
Show the character actively interacting with the important object,
character, or situation.

Panel 5:
Show the final action, consequence, transformation, escape, victory,
discovery, or resolution.

IMPORTANT IMAGE-PROMPT RULES:

Every image_prompt must explicitly contain:

1. The SAME character description.
2. The character's current action.
3. The important object involved in the scene.
4. The environment.
5. The camera shot/composition.
6. Lighting and atmosphere.
7. The requested visual art style.

Do NOT use vague phrases such as:
- "something happens"
- "interesting scene"
- "dramatic moment"
- "mysterious object"
- "the character reacts"

Instead describe exactly what should be visible in the image.

For example, do NOT write:

"Foxy discovers something mysterious."

Write something like:

"A sleek red fox with orange-red fur, white chest fur, black lower legs,
green eyes and a small blue collar stands beside a massive glowing blue
crystal embedded in an ancient tree trunk, one paw raised toward the crystal,
enchanted forest clearing, visible crystal occupying the right side of the
composition, medium-wide cinematic shot, blue and violet magical lighting,
realistic fantasy comic art."

The image prompt must describe things that can actually be seen.

IMPORTANT:
If the story contains a specific object, the object MUST be explicitly visible
in the image_prompt.

If the story contains an action, the action MUST be explicitly visible.

Examples:

"holding a flashlight" → show the character holding a flashlight.

"cutting a metal door with a plasma torch" → show the plasma torch touching
the metal door with visible sparks.

"touching a crystal" → show the character's hand/paw physically touching
the crystal.

"standing in a control room" → explicitly show the control room,
consoles and surrounding equipment.

Do not replace the requested action with a generic portrait of the character.

COMIC CONTINUITY:

The story should progress naturally:

Panel 1 → Setup
Panel 2 → Development
Panel 3 → Discovery / Main event
Panel 4 → Action / Conflict
Panel 5 → Resolution

Keep the same character identity, clothing, accessories and overall visual
style throughout the comic.

Generate EXACTLY 5 panels.

Each panel must contain:

- "panel" — integer 1 through 5
- "title" — short panel title
- "scene_description" — clear description of what happens
- "image_prompt" — detailed prompt for Stable Diffusion

The image_prompt should be approximately 60-120 words.

Respond ONLY with valid JSON.
Do not include explanations.
Do not use markdown code fences.

Expected format:

[
  {{
    "panel": 1,
    "title": "Panel title",
    "scene_description": "Clear description of the scene.",
    "image_prompt": "Detailed visual description..."
  }},
  {{
    "panel": 2,
    "title": "Panel title",
    "scene_description": "Clear description of the scene.",
    "image_prompt": "Detailed visual description..."
  }},
  {{
    "panel": 3,
    "title": "Panel title",
    "scene_description": "Clear description of the scene.",
    "image_prompt": "Detailed visual description..."
  }},
  {{
    "panel": 4,
    "title": "Panel title",
    "scene_description": "Clear description of the scene.",
    "image_prompt": "Detailed visual description..."
  }},
  {{
    "panel": 5,
    "title": "Panel title",
    "scene_description": "Clear description of the scene.",
    "image_prompt": "Detailed visual description..."
  }}
]
"""

    client = _get_client()

    max_retries = 3

    for attempt in range(max_retries):

        try:
            print(
                f"\n🤖 Generating comic outline "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            response = client.models.generate_content(
                model=GEMINI_FLASH_MODEL,
                contents=prompt,
            )

            output_text = (response.text or "").strip()

            print("\n🔵 RAW GEMINI RESPONSE 🔵")
            print(output_text)

            # ---------------------------------------------------------
            # Remove markdown code fences if Gemini adds them
            # ---------------------------------------------------------

            if output_text.startswith("```json"):
                output_text = output_text[7:]

                if output_text.endswith("```"):
                    output_text = output_text[:-3]

                output_text = output_text.strip()

            elif output_text.startswith("```"):
                output_text = output_text[3:]

                if output_text.endswith("```"):
                    output_text = output_text[:-3]

                output_text = output_text.strip()

            # ---------------------------------------------------------
            # Parse JSON
            # ---------------------------------------------------------

            panel_data = json.loads(output_text)

            if not isinstance(panel_data, list):
                raise ValueError(
                    "Gemini response is not a JSON list."
                )

            # ComicCraft requires exactly 5 panels

            if len(panel_data) != 5:
                raise ValueError(
                    f"Expected 5 panels, but Gemini returned "
                    f"{len(panel_data)} panels."
                )

            # ---------------------------------------------------------
            # Validate every panel
            # ---------------------------------------------------------

            required_keys = (
                "panel",
                "title",
                "scene_description",
                "image_prompt",
            )

            for expected_number, panel in enumerate(panel_data, start=1):

                if not isinstance(panel, dict):
                    raise ValueError(
                        f"Invalid panel format: {panel}"
                    )

                missing_keys = [
                    key
                    for key in required_keys
                    if key not in panel
                ]

                if missing_keys:
                    raise ValueError(
                        f"Panel {expected_number} is missing required "
                        f"keys: {missing_keys}"
                    )

                if panel["panel"] != expected_number:
                    raise ValueError(
                        f"Expected panel number {expected_number}, "
                        f"but received {panel['panel']}."
                    )

                if not isinstance(panel["title"], str):
                    raise ValueError(
                        f"Panel {expected_number} title must be a string."
                    )

                if not isinstance(panel["scene_description"], str):
                    raise ValueError(
                        f"Panel {expected_number} scene_description "
                        f"must be a string."
                    )

                if not isinstance(panel["image_prompt"], str):
                    raise ValueError(
                        f"Panel {expected_number} image_prompt "
                        f"must be a string."
                    )

                if not panel["image_prompt"].strip():
                    raise ValueError(
                        f"Panel {expected_number} image_prompt is empty."
                    )

            print("✅ Gemini outline generated successfully.")

            return panel_data

        # -------------------------------------------------------------
        # Invalid JSON
        # -------------------------------------------------------------

        except json.JSONDecodeError as e:

            print("❌ JSON Decode Error:", e)

            raise RuntimeError(
                f"Gemini returned invalid JSON: {e}"
            ) from e

        # -------------------------------------------------------------
        # Other errors
        # -------------------------------------------------------------

        except Exception as e:

            error_text = str(e)

            print(
                f"\n❌ Gemini attempt "
                f"{attempt + 1}/{max_retries} failed:"
            )
            print(error_text)

            # Retry temporary Gemini availability errors

            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < max_retries - 1:

                    delay = 2 ** attempt

                    print(
                        "⏳ Gemini is temporarily unavailable."
                    )

                    print(
                        f"🔄 Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)

                    continue

                raise RuntimeError(
                    "Gemini is temporarily unavailable after "
                    f"{max_retries} attempts. Please try again later."
                ) from e

            # Other errors should immediately be reported

            raise RuntimeError(
                f"Gemini outline generation failed: {error_text}"
            ) from e

    raise RuntimeError(
        "Gemini outline generation failed after all retry attempts."
    )