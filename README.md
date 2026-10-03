# FORGE Game Help

## Running with free local AI

1. Create and activate the project virtual environment:
   python -m venv venv
   source venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Install [Ollama](https://ollama.com/download) on the same computer/container
   running the app. If needed, run `ollama serve` in a separate terminal.
4. Download the local vision model (one-time download):
   ollama pull qwen2.5vl:3b
5. Copy the optional local settings:
   cp .env.example .env
6. Start the API:
   python -m app.main

Open http://localhost:8000 (or the forwarded port URL in VS Code) to use the game
help website. Enter a game title and question, optionally attach a JPEG, PNG, or
WebP gameplay screenshot (up to 8 MB), then choose a hint level from 1 to 10.
Level 1 is a subtle hint; level 10 requests a full step-by-step explanation.

The app searches configured public MediaWiki game wikis for relevant pages,
then asks Ollama running on your computer to answer using only retrieved
passages. Links to the cited pages are shown with each answer. Configured
sources currently cover Skyrim, Elden Ring, Breath of the Wild, Tears of the
Kingdom, Minecraft, Terraria, Hollow Knight, Genshin Impact, Fallout 3/4/New
Vegas/76, The Witcher 3, and Dark Souls. The current search uses game wikis; it
does not search Reddit or forums. Public wikis may not contain enough detail
for every question, so the app declines when it cannot find relevant evidence
rather than answer from model memory. No hosted AI or paid search API keys are
used, and the app has no prompt-count cap. Search queries go to the relevant
public wiki; text and optional screenshots are processed by your local Ollama
model. The one-time model download needs internet access and disk space; local
inference uses your computer's memory, processor/GPU, and electricity. Do not
treat this as unlimited hosted compute: the local model may be slow on machines
with limited memory.

`OLLAMA_BASE_URL` and `OLLAMA_MODEL` can be changed in `.env`. The default model
is `qwen2.5vl:3b`, which supports screenshot inputs as well as text.

The page's status indicator checks `/api/health`; the interactive API
documentation is available at `/docs`.