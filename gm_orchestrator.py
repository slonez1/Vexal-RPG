import os
import time
from typing import List, Tuple, Optional
import openai
from prompts import AUTO_SUMMARIZER_PROMPT, GM_PROMPT_TEMPLATE, STYLE_ECHO_INSTRUCTION
from utils import cosine_similarity
import numpy as np

# Configure via env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY environment variable.")
openai.api_key = OPENAI_API_KEY

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Core functions

def summarize_history(narrative_history: List[str], max_tokens: int = 300, target_words: int = 200) -> str:
    """
    Calls the LLM to produce a Memory Summary from narrative_history (oldest -> newest).
    Returns the summarized Memory Summary as a string.
    """
    history_joined = "\n\n".join(f"{i+1}) {entry}" for i, entry in enumerate(narrative_history))
    prompt = AUTO_SUMMARIZER_PROMPT.format(history=history_joined, max_tokens=max_tokens, target_words=target_words)
    resp = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are an automatic story summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def build_gm_prompt(memory_summary: str, recent_entries: List[str], target_words: int = 250, temperature: float = 0.25) -> str:
    """
    Build final GM prompt including memory summary and recent entries.
    recent_entries should be provided oldest->newest (but typically only the last 3-7 entries).
    """
    recent_joined = "\n\n".join(f"{i+1}) {entry}" for i, entry in enumerate(recent_entries))
    prompt = GM_PROMPT_TEMPLATE.format(
        memory_summary=memory_summary.strip(),
        recent_entries=recent_joined,
        target_words=target_words,
        temperature=temperature
    )
    # Append style echo instruction to help the model produce the initial style echo.
    prompt += "\n\n" + STYLE_ECHO_INSTRUCTION.strip()
    return prompt

def get_embedding(text: str) -> List[float]:
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding

def embedding_similarity(a_text: str, b_text: str) -> float:
    a_emb = get_embedding(a_text)
    b_emb = get_embedding(b_text)
    return cosine_similarity(a_emb, b_emb)

def generate_continuation(prompt: str, temperature: float = 0.25, max_tokens: int = 600) -> str:
    """
    Produce GM output (including style echo, continuation, GM note) from the chat model.
    """
    resp = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are the Game Master (GM) LLM for an ongoing interactive story. Preserve continuity and match style."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def run_gm_step(
    narrative_history: List[str],
    recent_n: int = 5,
    summary_max_tokens: int = 300,
    target_words: int = 250,
    temperature: float = 0.25,
    similarity_threshold: float = 0.78,
    max_attempts: int = 3,
) -> Tuple[str, str]:
    """
    Orchestrate: summarize -> build prompt -> generate -> style-check & retry if needed.

    Returns (final_memory_summary, final_generated_text)
    """
    if not narrative_history:
        raise ValueError("narrative_history must include at least one entry (oldest -> newest).")

    # 1) Auto-summarize whole history (or last M entries) to produce Memory Summary
    memory_summary = summarize_history(narrative_history, max_tokens=summary_max_tokens, target_words=target_words)
    # 2) Select last N recent entries to include verbatim in GM prompt
    recent_entries = narrative_history[-recent_n:] if len(narrative_history) >= recent_n else narrative_history[:]
    # 3) Build GM prompt
    gm_prompt = build_gm_prompt(memory_summary, recent_entries, target_words=target_words, temperature=temperature)

    # 4) Try generating, then check embedding similarity vs anchors (most recent entries)
    attempts = 0
    last_generation = None
    while attempts < max_attempts:
        attempts += 1
        gen = generate_continuation(gm_prompt, temperature=temperature, max_tokens=800)
        last_generation = gen

        # Extract the initial style echo and the rest (simple heuristic: first line is style echo)
        first_line = gen.splitlines()[0] if gen.strip() else ""
        # Compute average similarity between generation and each of the recent entries
        similarities = []
        for entry in recent_entries[-3:]:  # compare to up to last 3 anchors
            try:
                sim = embedding_similarity(first_line + "\n\n" + gen[:1000], entry)
            except Exception as e:
                sim = 0.0
            similarities.append(sim)
        avg_sim = float(np.mean(similarities)) if similarities else 0.0

        # Accept if similarity passes threshold
        if avg_sim >= similarity_threshold:
            return memory_summary, gen

        # Otherwise, tighten the prompt: lower temperature and add an explicit "match more closely" instruction
        temperature = max(0.05, temperature * 0.6)
        gm_prompt += f"\n\n[RETRY INSTRUCTION] The previous output drifted (similarity={avg_sim:.2f}). Match the Memory Summary and recent entries more closely; keep POV, tense, names, and sensory density consistent. Temperature for this attempt: {temperature:.2f}."
        time.sleep(0.5)  # small backoff

    # return last attempt even if it didn't pass
    return memory_summary, last_generation or ""

# Expose a simple CLI-friendly function
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run GM orchestrator step.")
    parser.add_argument("--history-file", help="Path to a text file with narrativeHistory entries separated by '---' lines.", required=True)
    args = parser.parse_args()
    with open(args.history_file, "r", encoding="utf-8") as fh:
        raw = fh.read()
    entries = [p.strip() for p in raw.split("\n---\n") if p.strip()]
    mem, out = run_gm_step(entries)
    print("=== MEMORY SUMMARY ===")
    print(mem)
    print("\n=== GM OUTPUT ===")
    print(out)
