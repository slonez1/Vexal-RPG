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

Files
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
