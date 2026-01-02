import streamlit as st
import json
import time
from datetime import datetime
#from game_state import advance_game_time
import sys
print("Python sys.path:", sys.path)
print("Current working directory:", os.getcwd())

st.title("Debugging: Vexal Engine UI")
st.write("If you see this, the app is loading.")

# Local modules
from data import INITIAL_GAME_STATE, MAT_PROPS
from game_state import (
    init_session_state,
    update_condition_timers,
    get_effective_stats,
    get_gs_copy,
    #advance_game_time,
    apply_time_spec,
    format_game_datetime
)
from ui_components import custom_bar, render_condition_badge
from gm_ai import get_gm_response, trigger_tts
import lore
from conditions import CONDITION_EFFECTS

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- CSS & TTS ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #0e1117; }
        .vexal-banner { background:#e83e8c; padding:6px 8px; border-radius:6px; font-weight:bold; color:white; text-align:center; margin-bottom:8px; }
        .attr-box { background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 5px; text-align: center; margin-bottom: 5px; }
        .attr-label { font-size: 0.55rem; color: #888; text-transform: uppercase; }
        .attr-val { font-size: 0.85rem; font-weight: bold; }
        .bar-container { background-color: #333; border-radius: 5px; height: 12px; width: 100%; margin-bottom: 10px; }
        .bar-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
        .debuff-badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 0.7rem; margin-right: 4px; margin-bottom: 4px; font-weight: bold; }
        .buff-badge { background-color: #28a745; color: white; }
        .debuff-badge-red { background-color: #ff4b4b; color: white; }
        .debuff-badge-orange { background-color: #ff9800; color: white; }
        .star { font-size: 1.2rem; }
        .chart-container { height: 300px; }
    </style>
    <script>
        function speak(text) {
            const msg = new SpeechSynthesisUtterance(text);
            msg.rate = 1.2;
            window.speechSynthesis.speak(msg);
        }
    </script>
""", unsafe_allow_html=True)

# --- SESSION INIT & LORE ---
init_session_state()
lore.init_lore()
gs = st.session_state.game_state

# when building save_data (serialize_lore_for_save already present)
# Replace the stray literal entries with guarded assignments so module import won't fail.
try:
    st.session_state['lore'] = lore_serial
except NameError:
    st.session_state.setdefault('lore', {})
# preserve last_llm_used if present, default False
st.session_state['last_llm_used'] = st.session_state.get('last_llm_used', False)

# --- SESSION STATE CLEANUP ---
MAX_MESSAGES = 50
if len(st.session_state.messages) > MAX_MESSAGES:
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# --- Update condition timers early so UI shows up-to-date values ---
update_condition_timers()

# --- EFFECTIVE STATS (cached) ---
gs_dict = get_gs_copy()
stats = get_effective_stats(gs_dict)
eff_attr = stats['attributes']
p_mod = stats['pool_mod']
hp_max_penalty = stats['hp_max_penalty']
stamina_drain = stats['stamina_drain']
