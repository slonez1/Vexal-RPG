import os
import openai
import time
import re
from typing import List, Generator

# Basic prompts (stream uses these)
AUTO_SUMMARIZER_PROMPT = """
You are an automatic story summarizer. Read the provided narrativeHistory entries (oldest first).
Produce a concise Memory Summary prioritizing facts the GM should remember and use.
Keep it short (approx. one paragraph up to ~250 words).
Output sections: Significant Events, Active Threads, Key NPCs & Relationships, Important Locations, Important Items/Artifacts, Recent Emotional Beats, Rules/Mechanics, Tone/Style brief, Use-guidance.
NarrativeHistory:
{history}
"""

GM_SYSTEM = "You are the Game Master (GM) LLM for an ongoing interactive story. Preserve continuity and match style."

GM_USER_TEMPLATE = """
Memory Summary:
{memory_summary}

Recent narrativeHistory (oldest → newest):
{recent_entries}

Task:
Continue the scene for approximately {target_words} words.
Begin with a 1-2 sentence style echo describing tone, sentence length, sensory density, and POV.
Push at least one Active Thread forward and mark any invented major facts with [new: ... — justification].
Do not contradict Memory Summary facts.
Keep temperature low and avoid long digressions. End at a natural beat and include a short GM note of unresolved hooks.
"""

# Configure OpenAI key via env
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_history(narrative_history: List[str], max_tokens: int = 300) -> str:
    history_joined = "\n\n".join(f"{i+1}) {entry}" for i, entry in enumerate(narrative_history))
    prompt = AUTO_SUMMARIZER_PROMPT.format(history=history_joined)
    resp = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": "You are an automatic story summarizer."},
                  {"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def build_gm_user_message(memory_summary: str, recent_entries: List[str], target_words: int=800) -> str:
    recent_joined = "\n\n".join(f"{i+1}) {entry}" for i, entry in enumerate(recent_entries))
    return GM_USER_TEMPLATE.format(memory_summary=memory_summary, recent_entries=recent_joined, target_words=target_words)

# Helper: yield text chunks from streaming response deltas
def stream_chat_completion_messages(system_content: str, user_content: str, temperature: float = 0.25, max_tokens: int = 1200) -> Generator[str, None, None]:
    """
    Calls OpenAI ChatCompletion streaming and yields incremental text deltas (joined).
    Each yielded value is the additional text delta received since last yield.
    """
    # Use ChatCompletion with stream=True
    # The exact streaming iterator shape may vary between SDK versions; this code assumes the standard iterator.
    response = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    buffer = ""
    for chunk in response:
        # Each chunk is a dict with 'choices' containing 'delta' possibly having 'content'.
        try:
            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            text = delta.get("content", "")
            if text:
                yield text
        except Exception:
            continue
    return
