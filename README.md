```markdown
# GM Orchestrator

This repository provides a lightweight Python orchestrator that implements the workflow described in the prompt:
- Auto-summarize recent narrativeHistory into a concise Memory Summary.
- Build a GM (Game Master) prompt that includes a style echo step, continuity checklist, and tie-ins to unresolved threads.
- Generate a continuation with low temperature to prevent drift.
- Optionally run an embedding-based style similarity check and retry/generate with tighter constraints if the output drifts.

Features
- Auto-summarizer prompt (configurable).
- GM prompt builder using recent entries and Memory Summary.
- Continuity checks and [new:] tagging behavior via prompt constraints.
- Embedding-based similarity check (OpenAI embeddings).
- Re-priming / retry loop with adjustable thresholds.

Requirements
- Python 3.10+
- OpenAI Python package (or compatible client)
- numpy

Installation
1. Create and activate a Python virtual environment.
2. Install dependencies:
   pip install -r requirements.txt

Configuration
- Set environment variable OPENAI_API_KEY (required).
- Optionally set OPENAI_CHAT_MODEL and OPENAI_EMBEDDING_MODEL.

Files```markdown
GM Stream + TTS Demo

This prototype streams incremental GM text from an LLM and synthesizes audio fragments with Google Cloud Text-to-Speech, delivering base64 audio chunks to a browser client which plays them via WebAudio for near-continuous playback.

Prerequisites
- Python 3.10+
- Google Cloud service account JSON with Text-to-Speech enabled. Set env var:
  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
- OpenAI API key set:
  - OPENAI_API_KEY=sk-...
- Optional: set OPENAI_CHAT_MODEL to a streaming-capable chat model (defaults to gpt-4o-mini). Use a model that supports streaming in your OpenAI tier.

Install
$ cd backend
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt

Environment variables
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcloud-key.json"
export OPENAI_API_KEY="sk-..."
# optionally
export OPENAI_CHAT_MODEL="gpt-4o-mini"

Run locally
$ cd backend
$ uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Open your browser at http://localhost:8000 and paste narrativeHistory lines, click Start.

Deployment notes (Cloud Run)
- You can containerize the backend and deploy to Cloud Run.
- For persistent caching across instances, use Google Cloud Storage (GCS) or Memorystore (Redis) — the prototype uses local disk caching which is ephemeral on Cloud Run.
- Ensure the Cloud Run service account has Text-to-Speech permission or use a service account key via GOOGLE_APPLICATION_CREDENTIALS (less recommended).

Next steps / improvements
- Replace base64 JSON audio frames with binary frames for lower overhead and higher throughput.
- Use SSML with Google TTS for richer prosody and consistent breathing/pauses.
- Use GCS for cache persistence and a cache index for pruning.
- Add authentication & rate-limiting for production.
- Optionally add multiple TTS providers and fallback logic (e.g., ElevenLabs) if you need more expressive voices.
```
- gm_orchestrator.py: Main orchestrator implementation.
- prompts.py: Prompt templates used for summarization and GM generation.
- utils.py: Helper functions (cosine similarity, token counting placeholder).
- example_usage.py: Example showing how to call the orchestrator.
- requirements.txt: Python dependencies.

Usage
- Import functions from gm_orchestrator and call `run_gm_step(...)` passing narrativeHistory entries (oldest -> newest).
- See `example_usage.py` for a runnable demonstration.

Notes & Safety
- The orchestrator uses prompts to enforce continuity, but it cannot fully prevent every form of narrative drift. Use the similarity thresholds and re-generation loop to tighten fidelity.
- This code contains prompt templates that you should adapt to your project's conventions and context.
```
