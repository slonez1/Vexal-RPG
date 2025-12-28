import streamlit as st
from copy import deepcopy
from data import INITIAL_GAME_STATE, MAT_PROPS
from conditions import CONDITION_EFFECTS
from datetime import datetime, timedelta

def init_session_state():
    """
    Initialize all session_state keys used by the app.
    Preserves existing data keys and backfills missing compatibility fields.
    Also attempts to load static lore files into the session lore repository once.
    """
    if "game_state" not in st.session_state:
        st.session_state.game_state = deepcopy(INITIAL_GAME_STATE)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "cmd_buffer" not in st.session_state:
        st.session_state.cmd_buffer = ""
    if "tts_enabled" not in st.session_state:
        st.session_state.tts_enabled = True
    if "condition_timers" not in st.session_state:
        st.session_state.condition_timers = {}
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "last_action_time" not in st.session_state:
        st.session_state.last_action_time = datetime.utcnow().isoformat()
    # Backfill skills_exp if absent
    gs = st.session_state.game_state
    if "skills_exp" not in gs:
        gs["skills_exp"] = {cat: {s: 0 for s in sks.keys()} for cat, sks in gs.get("skills", {}).items()}
    # Ensure canonical experience keys exist
    if "experience" not in gs:
        gs["experience"] = 0
    if "experience_next" not in gs:
        gs["experience_next"] = 100
    # Game time: persistent in game_state so saves include it
    if "game_datetime" not in gs:
        # Default in-game epoch (customizable)
        gs["game_datetime"] = datetime(1000, 1, 1, 8, 0).isoformat()
    if "hours_per_turn" not in gs:
        gs["hours_per_turn"] = 6  # default: 6 in-game hours per player turn

    # Initialize lore and then attempt to load static lore files into the session once.
    try:
        import lore as _lore
        _lore.init_lore()
        # load static files (idempotent)
        try:
            _lore.load_static_lore_files()
        except Exception as e:
            # log but don't break initialization
            st.session_state.setdefault("_lore_load_error", str(e))
    except Exception:
        # if lore can't be imported for some reason, skip gracefully
        pass

# ... rest of game_state.py unchanged (get_effective_stats, etc.)
