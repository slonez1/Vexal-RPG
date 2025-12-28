import streamlit as st
from game_state import update_condition_timers
from skills import gain_experience
import lore

def get_gm_response(prompt):
    """
    GM response stub: preserves original behavior and updates the lore repository.
    """
    update_condition_timers()
    if "use" in prompt.lower() or "cast" in prompt.lower():
        gain_experience(10)
    
    if "solve" in prompt.lower():
        st.success("Puzzle solved! You found a hidden passage.")

    # Example narrative (kept intentionally compact/predictable so parsing works)
    narrative = f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."
    # Auto-update lore heuristics from the narrative text
    try:
        lore.init_lore()
        lore.auto_extract_and_add(narrative)
    except Exception:
        # Non-fatal - do not block GM response
        pass

    return narrative

def trigger_tts(text):
    """
    Fire HTML5 TTS playback via st.components.v1.html if TTS enabled.
    """
    if st.session_state.get("tts_enabled", True):
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)
