import streamlit as st
from game_state import update_condition_timers, apply_time_spec
from skills import gain_experience
import lore
from datetime import datetime

def get_gm_response(prompt):
    """
    GM response stub: preserves original behavior and updates the lore repository.
    Calls LLM extraction and applies any time_advance specification returned by the extractor.
    """
    update_condition_timers()
    if "use" in prompt.lower() or "cast" in prompt.lower():
        gain_experience(10)
    
    if "solve" in prompt.lower():
        st.success("Puzzle solved! You found a hidden passage.")

    narrative = f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."

    # Use the LLM-backed extractor and capture returned extraction
    extracted = {}
    try:
        extracted = lore.llm_extract_and_add(narrative) or {}
    except Exception:
        # If something goes wrong, ensure at least heuristic parsing ran
        try:
            extracted = lore.auto_extract_and_add(narrative) or {}
        except Exception:
            extracted = {}

    # If extractor returned a time_advance hint, apply it
    time_spec = extracted.get("time_advance") or extracted.get("time") or {}
    if time_spec:
        try:
            apply_time_spec(time_spec)
        except Exception:
            # non-fatal
            pass

    # Return narrative (same as before)
    return narrative

def trigger_tts(text):
    """
    Fire HTML5 TTS playback via st.components.v1.html if TTS enabled.
    """
    if st.session_state.get("tts_enabled", True):
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)
