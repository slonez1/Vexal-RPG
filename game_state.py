import streamlit as st
from copy import deepcopy
from data import INITIAL_GAME_STATE, MAT_PROPS
from conditions import CONDITION_EFFECTS
from datetime import datetime

def init_session_state():
    """
    Initialize session_state keys used by the app.
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

def update_condition_timers():
    """Decrement timers and remove expired conditions from game_state."""
    expired = []
    for condition, turns_left in list(st.session_state.condition_timers.items()):
        if turns_left <= 0:
            expired.append(condition)
            if condition in st.session_state.game_state.get('conditions', {}):
                del st.session_state.game_state['conditions'][condition]
        else:
            st.session_state.condition_timers[condition] -= 1
    
    for cond in expired:
        if cond in st.session_state.condition_timers:
            del st.session_state.condition_timers[cond]

import streamlit as _st  # keep cache_data decoration available

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

    # Apply condition effects
    for condition in _gs_dict.get('conditions', {}).keys():
        if condition in CONDITION_EFFECTS:
            effects = CONDITION_EFFECTS[condition]['effects']
            # Apply attribute modifiers dynamically
            for attr in list(eff_attr.keys()):
                if attr in effects:
                    eff_attr[attr] += effects[attr]
            # All attributes modifier (Vexal)
            if 'all_attrs' in effects:
                for attr in eff_attr:
                    eff_attr[attr] += effects['all_attrs']
            pool_mod += effects.get('pool_penalty', 0)
            hp_max_penalty += effects.get('hp_max_penalty', 0)
            stamina_drain += effects.get('stamina_drain', 0)
            spell_cost_multiplier *= effects.get('spell_cost_multiplier', 1.0)
            movement_speed *= effects.get('movement_speed', 1.0)
            mana_regen *= effects.get('mana_regen', 1.0)
    
    # Armor Dex Penalties ONCE
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
