import streamlit as st
import json
import re
import time
from data import INITIAL_GAME_STATE, MAT_PROPS

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- CSS & TTS ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #0e1117; }
        .attr-box { background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 5px; text-align: center; margin-bottom: 5px; }
        .attr-label { font-size: 0.55rem; color: #888; text-transform: uppercase; }
        .attr-val { font-size: 0.85rem; font-weight: bold; }
        .bar-container { background-color: #333; border-radius: 5px; height: 12px; width: 100%; margin-bottom: 10px; }
        .bar-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
        .debuff-badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 0.7rem; margin-right: 4px; margin-bottom: 4px; font-weight: bold; }
        .buff-badge { background-color: #28a745; color: white; }
        .debuff-badge-red { background-color: #ff4b4b; color: white; }
        .debuff-badge-orange { background-color: #ff9800; color: white; }
    </style>
    <script>
        function speak(text) {
            const msg = new SpeechSynthesisUtterance(text);
            msg.rate = 1.2;
            window.speechSynthesis.speak(msg);
        }
    </script>
""", unsafe_allow_html=True)

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "cmd_buffer" not in st.session_state: 
    st.session_state.cmd_buffer = ""
if "tts_enabled" not in st.session_state: 
    st.session_state.tts_enabled = True
if "condition_timers" not in st.session_state:
    st.session_state.condition_timers = {}

gs = st.session_state.game_state

# --- SESSION STATE CLEANUP ---
MAX_MESSAGES = 50
if len(st.session_state.messages) > MAX_MESSAGES:
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# --- DEBUFF & BUFF SYSTEM ---
CONDITION_EFFECTS = {
    "Exhausted": {
        "color": "#ff4b4b",
        "desc": "Severe fatigue reduces DEX and CON by 5",
        "type": "debuff",
        "effects": {"DEX": -5, "CON": -5, "stamina_drain": 2}
    },
    "Fatigued": {
        "color": "#ff9800",
        "desc": "Mild exhaustion reduces DEX by 3",
        "type": "debuff",
        "effects": {"DEX": -3, "stamina_drain": 1}
    },
    "Wounded": {
        "color": "#d32f2f",
        "desc": "Physical damage reduces max HP by 20",
        "type": "debuff",
        "effects": {"hp_max_penalty": -20}
    },
    "Sprained Ankle": {
        "color": "#ff9800",
        "desc": "Movement penalty reduces DEX by 2",
        "type": "debuff",
        "effects": {"DEX": -2, "movement_speed": 0.5}
    },
    "Parched": {
        "color": "#f44336",
        "desc": "Mana regeneration slowed by 50%",
        "type": "debuff",
        "effects": {"mana_regen": 0.5}
    },
    "Divine Favor": {
        "
