# (top portion; keep the rest unchanged)
import streamlit as st
import json
import time
from datetime import datetime
from ..game_state import advance_game_time

# Local modules
from data import INITIAL_GAME_STATE, MAT_PROPS
from game_state import (
    init_session_state,
    update_condition_timers,
    get_effective_stats,
    get_gs_copy,
    advance_game_time,
    apply_time_spec,
    format_game_datetime
)
from ui_components import custom_bar, render_condition_badge
from gm_ai import get_gm_response, trigger_tts
import lore
from conditions import CONDITION_EFFECTS

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- CSS & TTS ---
st.markdown("""...""", unsafe_allow_html=True)  # keep existing CSS block

# --- SESSION INIT & LORE ---
init_session_state()
lore.init_lore()
gs = st.session_state.game_state

# when building save_data (serialize_lore_for_save already present)
# Guarded assignment to avoid syntax error at import time
try:
    st.session_state['lore'] = lore_serial
except NameError:
    st.session_state.setdefault('lore', {})
st.session_state['last_llm_used'] = st.session_state.get('last_llm_used', False)

# (rest of file unchanged)
