import streamlit as st
from game_state import update_condition_timers, apply_time_spec
from skills import gain_experience
import lore
from datetime import datetime
import gm_static

def get_gm_response(prompt):
    """
    Unified GM response entrypoint supporting three modes:
      - 'llm'       : try LLM-backed extraction (Gemini/GenAI) via lore.llm_extract_and_add
      - 'heuristic' : fallback lightweight parser lore.auto_extract_and_add
      - 'static'    : deterministic template-based gm_static.static_get_response
    The function sets st.session_state['last_llm_used'] to True when the LLM extractor was used.
    It returns a narrative string (the GM response).
    """
    update_condition_timers()

    # small gameplay experience: award experience for use/cast
    if "use" in prompt.lower() or "cast" in prompt.lower():
        gain_experience(10)

    if "solve" in prompt.lower():
        st.success("Puzzle solved! You found a hidden passage.")

    gs = st.session_state.game_state

    gm_mode = st.session_state.get("gm_mode", "llm")  # default to llm
    narrative = ""
    extracted = {}
    llm_used = False

    # Static mode: deterministic responses for testing
    if gm_mode == "static":
        narrative, extracted = gm_static.static_get_response(prompt, gs)
        llm_used = False

    # Heuristic mode: use the local heuristic extractor only
    elif gm_mode == "heuristic":
        narrative = f"Narrative: Amara acts upon '{prompt}'. (Heuristic parsing used)."
        extracted = lore.auto_extract_and_add(narrative) or {"source": "heuristic"}
        llm_used = False

    # LLM mode: try the LLM-backed extractor and fall back to heuristic.
    else:  # 'llm'
        narrative = f"Narrative: Amara acts upon '{prompt}'."
        try:
            extracted = lore.llm_extract_and_add(narrative) or {}
            # If the extractor returned a dict that didn't come from the heuristic fallback,
            # assume LLM was used. Our heuristic returns {"source":"heuristic"} when used.
            llm_used = not (extracted.get("source") == "heuristic")
        except Exception:
            # Safe fallback to heuristic if LLM fails
            extracted = lore.auto_extract_and_add(narrative) or {"source": "heuristic"}
            llm_used = False

    # Record for debugging / save export whether LLM was used
    st.session_state["last_llm_used"] = bool(llm_used)

    # If extractor returned a time_advance hint, apply it
    time_spec = {}
    if isinstance(extracted, dict):
        time_spec = extracted.get("time_advance") or extracted.get("time") or {}

    if time_spec:
        try:
            apply_time_spec(time_spec)
        except Exception:
            pass

    # Return a narrative. If not set by modes above, generate a fallback narrative.
    if not narrative:
        narrative = f"Narrative: Amara acts upon '{prompt}'. (No special handling.)"
    return narrative

def trigger_tts(text):
    """
    Fire HTML5 TTS playback via st.components.v1.html if TTS enabled.
    """
    if st.session_state.get("tts_enabled", True):
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)
