 import streamlit as st
from game_state import update_condition_timers
from skills import gain_experience

def get_gm_response(prompt):
    """
    Simple GM response stub that preserves original behaviour:
    - Updates condition timers
    - Awards experience for 'use'/'cast'
    - Handles puzzle 'solve' prompt
    Returns the same narrative string structure as the original.
    """
    # Ensure timers are decremented before handling response
    update_condition_timers()
    # Experience gain for actions
    if "use" in prompt.lower() or "cast" in prompt.lower():
        gain_experience(10)
    
    # Check for puzzle solutions
    if "solve" in prompt.lower():
        st.success("Puzzle solved! You found a hidden passage.")
    
    return f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."

def trigger_tts(text):
    """
    Fire HTML5 TTS playback via st.components.v1.html if TTS enabled.
    Preserves the escaping behaviour from the original file.
    """
    if st.session_state.get("tts_enabled", True):
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)
