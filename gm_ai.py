import streamlit as st
from game_state import update_condition_timers
from skills import gain_experience
import lore

def get_gm_response(prompt):
    """
    GM response stub: preserves original behavior and updates the lore repository.
    This version calls the LLM-backed lore extractor when keys are present.
    """
    update_condition_timers()
    if "use" in prompt.lower() or "cast" in prompt.lower():
        gain_experience(10)
    
    if "solve" in prompt.lower():
        st.success("Puzzle solved! You found a hidden passage.")

    narrative = f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."

    # Try LLM extraction first, fall back to heuristics (both functions update lore in session_state)
    try:
        lore.llm_extract_and_add(narrative)
    except Exception:
        try:
            lore.auto_extract_and_add(narrative)
        except Exception:
            # Non-fatal
            pass

    return narrative

def trigger_tts(text):
    """
    Fire HTML5 TTS playback via st.components.v1.html if TTS enabled.
    """
    if st.session_state.get("tts_enabled", True):
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)
