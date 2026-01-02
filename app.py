import streamlit as st
import json
import time
from datetime import datetime
from game_state import advance_game_time

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
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #0e1117; }
        .vexal-banner { background:#e83e8c; padding:6px 8px; border-radius:6px; font-weight:bold; color:white; text-align:center; margin-bottom:8px; }
        .attr-box { background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 5px; text-align: center; margin-bottom: 5px; }
        .attr-label { font-size: 0.55rem; color: #888; text-transform: uppercase; }
        .attr-val { font-size: 0.85rem; font-weight: bold; }
        .bar-container { background-color: #333; border-radius: 5px; height: 12px; width: 100%; margin-bottom: 10px; }
       
