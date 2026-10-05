# """
# Combines the generated images and the full comic story text into a single,
# ordered list of panel dictionaries ready for the preview page and the PDF
# exporter.
# """


# def build_comic_layout(image_paths: list, full_story: str, outline: list) -> list:
#     """
#     Organizes the generated images and full comic story into a structured layout.

#     Args:
#         image_paths (list): List of image file paths, one per panel, in
#                              the same order as `outline`.
#         full_story (str): The complete generated comic story text, formatted
#                            as one "**Panel N: Title**" block per panel (see
#                            gemini_pro.generate_story).
#         outline (list): The panel outline data from generate_outline().

#     Returns:
#         list: A list of dictionaries, one per panel, each containing
#               "panel", "title", "image_path", "text" (caption/narration/
#               image-prompt lines), and "scene_description".
#     """
#     # Split the full story into individual panel segments
#     story_panels = full_story.split("**Panel")
#     story_panels = [f"**Panel{panel}" for panel in story_panels if panel.strip()]

#     # Build layout panel by panel
#     layout = []
#     for idx, (image, text, panel_info) in enumerate(
#         zip(image_paths, story_panels, outline), start=1
#     ):
#         layout.append({
#             "panel": idx,
#             "title": panel_info.get("title", f"Panel {idx}"),
#             "image_path": image,
#             # Remove the "**Panel N: Title**" header line, keep the rest.
#             "text": "\n".join(text.strip().splitlines()[1:]).strip(),
#             "scene_description": panel_info.get("scene_description", ""),
#         })

#     return layout

"""
Combines generated images and readable comic story text into an ordered
list of panel dictionaries ready for the preview page and PDF exporter.
"""

import re


def _clean_story_text(text: str) -> str:
    """
    Removes internal image-generation instructions if Gemini accidentally
    returns them.
    """

    # Remove IMAGE PROMPT sections if they somehow appear.
    text = re.sub(
        r"\*\*IMAGE PROMPT:\*\*.*?(?=\n\*\*Panel|\Z)",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove accidental markdown code fences.
    text = text.replace("```", "")

    return text.strip()


def build_comic_layout(
    image_paths: list,
    full_story: str,
    outline: list,
) -> list:
    """
    Organizes generated images and readable comic narration.

    Each returned panel contains:

    - panel
    - title
    - image_path
    - text
    - scene_description
    """

    # Split story using Panel headers.
    matches = list(
        re.finditer(
            r"\*\*Panel\s+(\d+):\s*(.*?)\*\*",
            full_story,
            flags=re.IGNORECASE,
        )
    )

    story_panels = []

    for index, match in enumerate(matches):
        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(full_story)

        panel_number = int(match.group(1))
        panel_title = match.group(2).strip()

        panel_body = full_story[start:end].strip()

        story_panels.append(
            {
                "panel": panel_number,
                "title": panel_title,
                "text": _clean_story_text(panel_body),
            }
        )

    layout = []

    for idx, (image, panel_info) in enumerate(
        zip(image_paths, outline),
        start=1,
    ):
        story_info = next(
            (
                item
                for item in story_panels
                if item["panel"] == idx
            ),
            None,
        )

        if story_info:
            story_text = story_info["text"]
            title = story_info["title"]
        else:
            story_text = ""
            title = panel_info.get(
                "title",
                f"Panel {idx}",
            )

        layout.append(
            {
                "panel": idx,
                "title": title,
                "image_path": image,
                "text": story_text,
                "scene_description": panel_info.get(
                    "scene_description",
                    "",
                ),
            }
        )

    return layout