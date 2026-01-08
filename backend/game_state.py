import streamlit as st
from copy import deepcopy
from data import INITIAL_GAME_STATE, MAT_PROPS
from conditions import CONDITION_EFFECTS
from datetime import datetime, timedelta

def init_session_state():
    """
    Initialize all session_state keys used by the app.
    Preserves existing data keys and backfills missing compatibility fields.
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

    gs = st.session_state.game_state
    if "skills_exp" not in gs:
        gs["skills_exp"] = {cat: {s: 0 for s in sks.keys()} for cat, sks in gs.get("skills", {}).items()}
    if "experience" not in gs:
        gs["experience"] = 0
    if "experience_next" not in gs:
        gs["experience_next"] = 100
    if "game_datetime" not in gs:
        gs["game_datetime"] = datetime(1000, 1, 1, 8, 0).isoformat()
    if "hours_per_turn" not in gs:
        gs["hours_per_turn"] = 6

def update_condition_timers():
    """Decrement timers and remove expired conditions from game_state."""
    expired = []
    timers = st.session_state.get("condition_timers", {})
    for condition, turns_left in list(timers.items()):
        try:
            if int(turns_left) <= 0:
                expired.append(condition)
                if condition in st.session_state.game_state.get('conditions', {}):
                    del st.session_state.game_state['conditions'][condition]
            else:
                st.session_state.condition_timers[condition] = int(turns_left) - 1
        except Exception:
            # ignore malformed values
            continue

    for cond in expired:
        if cond in st.session_state.condition_timers:
            del st.session_state.condition_timers[cond]

import streamlit as _st  # for cache_data decorator

@_st.cache_data(ttl=1, show_spinner=False)
def get_effective_stats(_gs_dict):
    """
    Cached calculation of effective stats with all modifiers.
    """
    eff_attr = _gs_dict['attributes'].copy()
    pool_mod = 0
    hp_max_penalty = 0
    stamina_drain = 0
    spell_cost_multiplier = 1.0
    movement_speed = 1.0
    mana_regen = 1.0

    for condition in _gs_dict.get('conditions', {}).keys():
        if condition in CONDITION_EFFECTS:
            effects = CONDITION_EFFECTS[condition].get('effects', {})
            for attr in list(eff_attr.keys()):
                if attr in effects:
                    eff_attr[attr] += effects[attr]
            if 'all_attrs' in effects:
                for attr in eff_attr:
                    eff_attr[attr] += effects['all_attrs']
            pool_mod += effects.get('pool_penalty', 0)
            hp_max_penalty += effects.get('hp_max_penalty', 0)
            stamina_drain += effects.get('stamina_drain', 0)
            spell_cost_multiplier *= effects.get('spell_cost_multiplier', 1.0)
            movement_speed *= effects.get('movement_speed', 1.0)
            mana_regen *= effects.get('mana_regen', 1.0)

    for slot in ['Head', 'Torso', 'Legs', 'Hands', 'OffHand']:
        item = _gs_dict.get('equipment', {}).get(slot)
        if item and item.get('type') == 'Armor':
            mat = item.get('material')
            eff_attr['DEX'] += MAT_PROPS.get(mat, {}).get('Dex_Penalty', 0)

    return {
        'attributes': eff_attr,
        'pool_mod': pool_mod,
        'hp_max_penalty': hp_max_penalty,
        'stamina_drain': stamina_drain,
        'spell_cost_multiplier': spell_cost_multiplier,
        'movement_speed': movement_speed,
        'mana_regen': mana_regen
    }

def get_gs_copy():
    """Return a shallow dict copy of the live game_state for caching calls and safe reads."""
    return dict(st.session_state.game_state)

# ----------------- In-Game Time Utilities -----------------
def parse_game_datetime(gs):
    """Return a datetime from the stored ISO string in game_state (gs dict)."""
    val = gs.get("game_datetime")
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return datetime(1000, 1, 1, 8, 0)

def format_game_datetime(gs):
    """Return a human-friendly in-game date/time string."""
    dt = parse_game_datetime(gs)
    return dt.strftime("Year %Y-%m-%d %H:%M")

def advance_game_time(turns=1):
    """
    Advance in-game time by (hours_per_turn * turns) hours, persists to session_state.game_state.
    Returns the new formatted time.
    """
    gs = st.session_state.game_state
    hours = float(gs.get("hours_per_turn", 6)) * max(1, int(turns))
    dt = parse_game_datetime(gs)
    dt += timedelta(hours=hours)
    gs["game_datetime"] = dt.isoformat()
    # increment turn counter and timestamp
    st.session_state["turn_count"] = st.session_state.get("turn_count", 0) + max(1, int(turns))
    st.session_state["last_action_time"] = datetime.utcnow().isoformat()
    return format_game_datetime(gs)

def advance_game_time_delta(hours=0, seconds=0):
    """Advance in-game time by an arbitrary hours and seconds delta, persist to game_state."""
    gs = st.session_state.game_state
    dt = parse_game_datetime(gs)
    dt += timedelta(hours=hours, seconds=seconds)
    gs["game_datetime"] = dt.isoformat()
    st.session_state["last_action_time"] = datetime.utcnow().isoformat()
    return format_game_datetime(gs)

def apply_time_spec(time_spec):
    """
    Accepts a structured time spec (dict) and applies it.
    Returns the formatted new game_datetime.
    """
    gs = st.session_state.game_state
    if not isinstance(time_spec, dict):
        return format_game_datetime(gs)
    if "hours_per_turn" in time_spec:
        try:
            gs["hours_per_turn"] = float(time_spec["hours_per_turn"])
        except Exception:
            pass
    seconds = int(time_spec.get("seconds", 0) or 0)
    hours = float(time_spec.get("hours", 0) or 0.0)
    if "scale" in time_spec:
        if time_spec["scale"] == "combat":
            seconds = int(time_spec.get("seconds_per_turn", time_spec.get("seconds", 6)))
        if time_spec["scale"] == "travel":
            hours = float(time_spec.get("hours_per_turn", time_spec.get("hours", gs.get("hours_per_turn", 6))))
    if seconds:
        return advance_game_time_delta(seconds=seconds)
    if hours:
        return advance_game_time_delta(hours=hours)
    return advance_game_time(turns=1)
