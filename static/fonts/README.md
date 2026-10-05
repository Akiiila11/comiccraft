# Fonts folder

`app/exporters.py` looks for `static/fonts/DejaVuSans.ttf` when it builds
the PDF export.

- **If the file is present:** the PDF uses DejaVu Sans, a Unicode TTF font,
  so any character Gemini generates (smart quotes, accents, em dashes,
  emoji-adjacent punctuation, etc.) renders correctly.
- **If it's absent (the default, since the font isn't bundled here to keep
  this download small):** the exporter automatically falls back to a
  built-in core font (Helvetica) and transliterates text to Latin-1. The
  app still runs and produces a valid PDF either way — you just won't get
  full Unicode support without the font.

To add full Unicode support, download `DejaVuSans.ttf` (SIL Open Font
License) from https://dejavu-fonts.github.io/ and place it in this folder.
No code changes are needed — it will be picked up automatically the next
time you export a comic.
