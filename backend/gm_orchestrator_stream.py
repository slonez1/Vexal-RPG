import os
import openai
from typing import List, Generator

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_history(narrative_history: List[str], max_tokens: int = 300) -> str:
    history_joined = "\n\n".join(f"{i+1}) {entry}" for i, entry in enumerate(narrative_history))
    prompt = f"Summarize the important facts and threads from the following history. Keep concise.\n\n{history_joined}"
    resp = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def build_gm_user_message(memory_summary: str, recent_entries: List[str], target_words: int=800) -> str:
    recent_joined = "\n\n".join(recent_entries)
    return f"Memory Summary:\n{memory_summary}\n\nRecent entries:\n{recent_joined}\n\nContinue the scene for approx {target_words} words. Start with a 1-2 sentence style echo. Tie an Active Thread forward."

def stream_chat_completion_messages(system_content: str, user_content: str, temperature: float = 0.25, max_tokens: int = 1200) -> Generator[str, None, None]:
    # Use OpenAI streaming; each chunk contains incremental content delta
    resp = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[{"role":"system","content":system_content},{"role":"user","content":user_content}],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    for chunk in resp:
        try:
            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            if "content" in delta:
                yield delta["content"]
        except Exception:
            continue
