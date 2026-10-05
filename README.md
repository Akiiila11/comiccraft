# ComicCraft — AI Comic Story Creator

Turns a story prompt into a personalized, panel-by-panel comic: Gemini
writes the outline and narration, Stable Diffusion illustrates each panel,
and the whole thing is exported as a downloadable PDF — all from a small
FastAPI app with a simple HTML/Jinja2 frontend.

```
comiccraft/
├── app/
│   ├── main.py            # FastAPI app entrypoint
│   ├── routes.py          # All routes (/, /generate, /generate-comic/json, ...)
│   ├── config.py          # Env vars, model names, folder paths
│   ├── gemini_flash.py     # generate_outline() — 5-panel outline
│   ├── gemini_pro.py       # generate_story() — narration & dialogue
│   ├── image_generator.py # generate_image() — Stable Diffusion panels
│   ├── layout_builder.py  # build_comic_layout() — combine story + images
│   └── exporters.py       # save_pdf() — compile the final PDF
├── templates/              # index.html, comic_preview.html, export_success.html
├── static/
│   ├── panels/             # generated panel images land here
│   ├── exports/            # generated comic PDFs land here
│   └── fonts/               # optional Unicode font for PDF export
├── tests/
│   └── test_app.py         # offline smoke tests (AI calls are mocked)
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── pytest.ini
```

> **A note on the AI models used here.** The original project spec named
> Gemini 1.5 Flash/Pro and `runwayml/stable-diffusion-v1-5`. Both have
> since been retired/removed by their providers, so this build uses their
> current replacements instead (Gemini's rolling `-latest` model aliases,
> and the maintained `stable-diffusion-v1-5/stable-diffusion-v1-5` mirror
> on Hugging Face). See `.env.example` if you ever want to pin different
> model names.

---

## 1. Prerequisites

- **Python 3.10–3.12** installed and on your PATH
- **VS Code** with the official **Python extension** (ms-python.python)
- A **Gemini API key** — free at https://aistudio.google.com/app/apikey
- (Optional but recommended) An **NVIDIA GPU with CUDA** for fast image
  generation. Stable Diffusion will also run on CPU, just much more slowly
  (several minutes per image instead of a few seconds).

---

## 2. Open the project in VS Code

1. Unzip the project folder anywhere on your machine.
2. In VS Code: **File → Open Folder…** → select the `comiccraft` folder
   (the one containing `app/`, `templates/`, `requirements.txt`, etc.).
3. VS Code may prompt "This folder contains a virtual environment / do you
   want to select an interpreter?" — you can dismiss this for now; we'll
   create the environment in the next step.

---

## 3. Create a virtual environment and install dependencies

Open a terminal in VS Code (**Terminal → New Terminal**), which opens
already at the project root, and run:

```bash
# Create the virtual environment
python -m venv env

# Activate it
# Windows (PowerShell):
env\Scripts\Activate.ps1
# Windows (cmd.exe):
env\Scripts\activate.bat
# macOS/Linux:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then, in VS Code, select this environment as your interpreter:
**Ctrl+Shift+P** (or **Cmd+Shift+P** on macOS) → **"Python: Select
Interpreter"** → choose the one under `./env`.

**GPU users:** if `pip install -r requirements.txt` gives you a CPU-only
PyTorch build and you have an NVIDIA GPU, install the matching CUDA build
of `torch` first using the selector at
https://pytorch.org/get-started/locally/, then re-run
`pip install -r requirements.txt` to pick up the rest.

---

## 4. Configure your API key

```bash
# macOS/Linux
cp .env.example .env
# Windows
copy .env.example .env
```

Open the new `.env` file and set:

```
GEMINI_API_KEY=your_real_key_here
```

Leave the other values as-is unless you specifically want to pin a
different Gemini model or a different Stable Diffusion checkpoint.

---

## 5. Run the app

From the project root, with your virtual environment activated:

```bash
uvicorn app.main:app --reload
```

You should see Uvicorn start up and log something like
`Uvicorn running on http://127.0.0.1:8000`.

Then open in your browser:

- **App:** http://127.0.0.1:8000
- **Interactive API docs (Swagger UI):** http://127.0.0.1:8000/docs

Fill in the form on the homepage (story prompt, character name, setting,
tone, art style) and click **Generate Comic**.

> ⏳ **First run will be slow.** The first time `generate_image()` runs,
> `diffusers` downloads the Stable Diffusion model weights (a few GB),
> then loads them onto your GPU/CPU. This can take several minutes.
> Subsequent generations are much faster since the model stays loaded in
> memory for the life of the server process.

### API endpoints

All of these are also listed and testable at `/docs`:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Homepage with the story input form |
| POST | `/generate` | Form submission → generates the comic → shows the preview page |
| POST | `/generate-comic/json` | Same pipeline, for JSON API clients (see body shape in `/docs`) |
| GET | `/export-success` | Confirmation page shown after downloading a PDF |
| GET | `/test-image` | Developer utility: generate a single test image directly |

---

## 6. Run the tests

The test suite mocks the Gemini and Stable Diffusion calls, so it runs in
a couple of seconds — no API key, no GPU, and no internet connection
needed for testing:

```bash
pip install -r requirements-dev.txt
pytest
```

You should see 6 passing tests, covering: the homepage loading, the form
submission pipeline, the JSON API pipeline (including that a real PDF
file is written to disk), the `/test-image` route, and the export-success
page.

---

## 7. Troubleshooting

- **`GEMINI_API_KEY is not set` error when generating a comic** — make
  sure you created `.env` (step 4) and that it sits in the project root,
  next to `requirements.txt`.
- **`ModuleNotFoundError: No module named 'app'`** — make sure your
  terminal's current directory is the project root (the folder
  containing `app/`, not inside it) when you run `uvicorn` or `pytest`.
- **Image generation is very slow / seems frozen** — this is expected on
  CPU-only machines; check the terminal log for
  `🎨 Loading Stable Diffusion pipeline...` to confirm it's working, just
  slowly. A GPU makes this dramatically faster.
- **PDF text looks garbled for non-English or special characters** — see
  `static/fonts/README.md` to add a Unicode font; the app runs fine
  without it, just with reduced character support in the PDF.
- **Port 8000 already in use** — run
  `uvicorn app.main:app --reload --port 8001` instead, and use that port
  in your browser.
