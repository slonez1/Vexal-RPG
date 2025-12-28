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
        "color": "#ffd700",
        "desc": "Blessed by divine power - 25% mana cost reduction",
        "type": "buff",
        "effects": {"spell_cost_multiplier": 0.75}
    },
    "Blessed": {
        "color": "#28a745",
        "desc": "Holy protection increases WIS by 3",
        "type": "buff",
        "effects": {"WIS": 3}
    },
    "Haste": {
        "color": "#00bcd4",
        "desc": "Supernatural speed increases DEX by 4",
        "type": "buff",
        "effects": {"DEX": 4, "movement_speed": 1.5}
    },
    "Vexal Active": {
        "color": "#e83e8c",
        "desc": "Corrupting influence suppresses all attributes",
        "type": "debuff",
        "effects": {"all_attrs": -2, "pool_penalty": -20}
    }
}

# --- CONDITION TIMER MANAGEMENT ---
def update_condition_timers():
    """Decrement timers and remove expired conditions"""
    expired = []
    for condition, turns_left in st.session_state.condition_timers.items():
        if turns_left <= 0:
            expired.append(condition)
            if condition in gs['conditions']:
                del gs['conditions'][condition]
        else:
            st.session_state.condition_timers[condition] -= 1
    
    for cond in expired:
        del st.session_state.condition_timers[cond]

# --- GM AI & TTS ---
def get_gm_response(prompt):
    update_condition_timers()  # Decrement timers on each action
    return f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."

def trigger_tts(text):
    if st.session_state.tts_enabled:
        # Optimized TTS with faster rate
        clean_text = text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(f"<script>speak('{clean_text}');</script>", height=0)

# --- MATH ENGINE: FIXED DEX CALCULATION WITH BUFFS/DEBUFFS ---
@st.cache_data(ttl=1, show_spinner=False)
def get_effective_stats(_gs_dict):
    """Cached calculation of effective stats with all modifiers"""
    eff_attr = _gs_dict['attributes'].copy()
    pool_mod = 0
    hp_max_penalty = 0
    stamina_drain = 0
    spell_cost_multiplier = 1.0
    movement_speed = 1.0
    mana_regen = 1.0
    
    # Apply condition effects
    for condition in _gs_dict['conditions'].keys():
        if condition in CONDITION_EFFECTS:
            effects = CONDITION_EFFECTS[condition]['effects']
            
            # Attribute modifiers
            for attr in ['STR', 'DEX', 'CON', 'WIS', 'CHA']:
                if attr in effects:
                    eff_attr[attr] += effects[attr]
            
            # All attributes modifier (Vexal)
            if 'all_attrs' in effects:
                for attr in eff_attr:
                    eff_attr[attr] += effects['all_attrs']
            
            # Pool penalties
            if 'pool_penalty' in effects:
                pool_mod += effects['pool_penalty']
            
            if 'hp_max_penalty' in effects:
                hp_max_penalty += effects['hp_max_penalty']
            
            if 'stamina_drain' in effects:
                stamina_drain += effects['stamina_drain']
            
            if 'spell_cost_multiplier' in effects:
                spell_cost_multiplier *= effects['spell_cost_multiplier']
            
            if 'movement_speed' in effects:
                movement_speed *= effects['movement_speed']
            
            if 'mana_regen' in effects:
                mana_regen *= effects['mana_regen']
    
    # Apply Armor DEX Penalties ONCE
    for slot in ['Head', 'Torso', 'Legs', 'Hands', 'OffHand']:
        if slot in _gs_dict['equipment'] and _gs_dict['equipment'][slot].get('type') == 'Armor':
            mat = _gs_dict['equipment'][slot]['material']
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

# Convert gs to dict for caching (session_state objects aren't hashable)
gs_dict = dict(gs)
stats = get_effective_stats(gs_dict)
eff_attr = stats['attributes']
p_mod = stats['pool_mod']
hp_max_penalty = stats['hp_max_penalty']
stamina_drain = stats['stamina_drain']
spell_cost_multiplier = stats['spell_cost_multiplier']
movement_speed = stats['movement_speed']
mana_regen = stats['mana_regen']

cur_hp_m = gs['hp_max'] + p_mod + hp_max_penalty
cur_sta_m = gs['stamina_max'] + p_mod
cur_mana_m = gs['mana_max'] + p_mod

# Apply stamina drain
gs['stamina'] = max(0, gs['stamina'] - stamina_drain)

# --- SIDEBAR (IMMUTABLE) ---
def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.sidebar.markdown(f"<div style='display:flex;justify-content:space-between;font-size:0.7rem;font-weight:bold;margin-bottom:2px;'><span>{label}</span><span>{int(current)}/{maximum}</span></div><div class='bar-container'><div class='bar-fill' style='width:{percent}%;background-color:{color};'></div></div>", unsafe_allow_html=True)

with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    custom_bar("❤️ HEALTH", gs['hp'], cur_hp_m, "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], cur_sta_m, "#28a745")
    custom_bar("✨ MANA", gs['mana'], cur_mana_m, "#007bff")
    st.markdown("<hr style='border:1px solid #444;margin:15px 0;'>", unsafe_allow_html=True)
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    # Active Conditions Display
    if gs['conditions']:
        st.markdown("**Active Effects:**")
        for condition in gs['conditions'].keys():
            if condition in CONDITION_EFFECTS:
                cond_data = CONDITION_EFFECTS[condition]
                badge_class = "buff-badge" if cond_data['type'] == "buff" else "debuff-badge-red"
                timer_text = ""
                if condition in st.session_state.condition_timers:
                    timer_text = f" ({st.session_state.condition_timers[condition]} turns)"
                st.markdown(f"<span class='debuff-badge {badge_class}'>{condition}{timer_text}</span>", unsafe_allow_html=True)
    
    st.write("### Attributes")
    a_cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff_attr[attr]
        diff = val - base
        clr = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        sign = "+" if diff > 0 else ""
        a_cols[i%3].markdown(f"<div class='attr-box'><div class='attr-label'>{attr}</div><div class='attr-val' style='color:{clr};'>{val} ({sign}{diff})</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"**Vaxel:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)
    
    # Movement Speed Indicator
    if movement_speed != 1.0:
        speed_pct = int(movement_speed * 100)
        speed_color = "#28a745" if movement_speed > 1.0 else "#ff4b4b"
        st.markdown(f"**🏃 Movement:** <span style='color:{speed_color};'>{speed_pct}%</span>", unsafe_allow_html=True)

# --- TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_stat:
    # 1. Condition Overview
    st.subheader("🩹 Active Conditions")
    if not gs['conditions']:
        st.info("Amara is currently free of any debilitating conditions.")
    else:
        for condition, effect in gs['conditions'].items():
            if condition in CONDITION_EFFECTS:
                cond_data = CONDITION_EFFECTS[condition]
                timer_info = ""
                if condition in st.session_state.condition_timers:
                    timer_info = f" - **{st.session_state.condition_timers[condition]} turns remaining**"
                
                if cond_data['type'] == "buff":
                    st.success(f"✨ **{condition}**: {cond_data['desc']}{timer_info}")
                else:
                    st.warning(f"⚠️ **{condition}**: {cond_data['desc']}{timer_info}")
            else:
                st.warning(f"**{condition}**: {effect}")

    st.divider()

    # 2. Saving Throws Logic
    st.subheader("🎲 Saving Throws")
    st.caption("Base defense against physical, mental, and magical hazards.")
    
    save_cols = st.columns(3)
    save_list = [
        ("Fortitude", "CON", "Physical resilience"),
        ("Reflex", "DEX", "Reaction speed"),
        ("Willpower", "WIS", "Mental fortitude"),
        ("Acrobatics", "DEX", "Balance and poise"),
        ("Insight", "WIS", "Detecting deception"),
        ("Presence", "CHA", "Force of personality")
    ]

     level_bonus = gs['level'] // 2
    for i, (save_name, attr_key, hint) in enumerate(save_list):
        total_save = eff_attr[attr_key] + level_bonus
        with save_cols[i % 3]:
            st.metric(
                label=save_name, 
                value=f"+{total_save}", 
                delta=f"Attr: {eff_attr[attr_key]} | Lvl: {level_bonus}",
                delta_color="off",
                help=hint
            )

    st.divider()

    # 3. Vexal State Mechanics
    st.subheader("🧬 Vexal Influence Breakdown")
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        st.markdown("**Attribute Suppression:**")
        st.code("-2 to all Base Attributes (Applied)", language="diff")
        st.markdown("**Pool Suppression:**")
        st.code("-20 Max HP\n-20 Max Stamina\n-20 Max Mana", language="diff")

    with v_col2:
        st.markdown(f"**Subjugation Peak:** `{gs['orgasm_count']}/10` overflows")
        peak_progress = (gs['orgasm_count'] / 10)
        st.progress(peak_progress)
        if gs['orgasm_count'] >= 7:
            st.error("⚠️ HIGH RISK: Vexal state nearing Subjugation threshold.")
        else:
            st.success("Vexal state currently manageable.")

    # 4. Resistances
    st.divider()
    st.subheader("🛡️ Resistances")
    r_col1, r_col2, r_col3 = st.columns(3)
    r_col1.write("**Holy:** 25%")
    r_col2.write("**Void:** -10%")
    r_col3.write("**Physical:** 5%")
    
    # 5. Spell Cost Modifiers
    if spell_cost_multiplier != 1.0:
        st.divider()
        st.subheader("✨ Spell Casting Modifiers")
        cost_pct = int(spell_cost_multiplier * 100)
        if spell_cost_multiplier < 1.0:
            st.success(f"🌟 Divine Favor Active: Spell costs reduced to **{cost_pct}%**")
        else:
            st.warning(f"⚠️ Spell costs increased to **{cost_pct}%**")

with tab_con:
    c_win = st.container(height=350)
    with c_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): 
                st.markdown(m["content"])
    
    st.write("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        sk_list = sorted([s for cat in gs['skills'].values() for s in cat.keys()])
        sk = st.selectbox("Skills", sk_list, label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sk}] "
            st.rerun()
    with d2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Spell: {sp}] "
            st.rerun()
    with d3:
        imp = st.text_input("Impromptu", placeholder="Action...", label_visibility="collapsed")
        if st.button("🚀 Execute", use_container_width=True):
            if imp:
                full = f"🛠️ [IMPROMPTU]: {imp}"
                st.session_state.messages.append({"role": "user", "content": full})
                res = get_gm_response(full)
                st.session_state.messages.append({"role": "assistant", "content": res})
                trigger_tts(res)
                st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        full = st.session_state.cmd_buffer + direct
        st.session_state.messages.append({"role": "user", "content": full})
        st.session_state.cmd_buffer = ""
        res = get_gm_response(full)
        st.session_state.messages.append({"role": "assistant", "content": res})
        trigger_tts(res)
        st.rerun()

with tab_char:
    st.subheader("Mastered Skills")
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Mastery"):
            c1, c2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): 
                (c1 if i%2==0 else c2).write(f"**{s}**: {r}")
    
    st.divider()
    st.subheader("✨ Spellbook")
    sp1, sp2 = st.columns(2)
    for i, spn in enumerate(gs['known_spells']):
        base_cost = gs['mana_costs'].get(spn, 0)
        effective_cost = int(base_cost * spell_cost_multiplier)
        cost_display = f"{effective_cost} MP"
        if effective_cost != base_cost:
            cost_display += f" (base: {base_cost})"
        (sp1 if i%2==0 else sp2).info(f"**{spn}** ({cost_display})")

with tab_inv:
    st.subheader("Equipment Detail")
    for slot, d in gs['equipment'].items():
        with st.container(border=True):
            props = MAT_PROPS.get(d['material'], {})
            st.markdown(f"**Slot:** `{slot}` | **Item:** {d['item']} | **Material:** {d['material']}")
            col_a, col_b, col_c = st.columns(3)
            col_a.write(f"🛡️ AC (DT): {props.get('DT', 'N/A')}")
            col_b.write(f"⚖️ Weight: {props.get('Weight', '0')} lbs")
            col_c.write(f"🔊 Noise: {props.get('Noise', '0')}")
            st.progress(d['cond']/100, text=f"Condition: {d['cond']}%")

with tab_sett:
    st.subheader("🛠️ System Controls")
    
    # 1. UNDO TURN
    if st.button("⬅️ UNDO LAST TURN", use_container_width=True, help="Reverts the last player action and GM response."):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
        else:
            st.toast("No turns left to undo!", icon="🚫")

    # 2. CONDITION MANAGEMENT
    st.divider()
    st.subheader("🩹 Condition Manager")
    
    col_add, col_remove = st.columns(2)
    
    with col_add:
        st.markdown("**Add Condition:**")
        new_cond = st.selectbox("Select Condition", list(CONDITION_EFFECTS.keys()), key="add_cond")
        duration = st.number_input("Duration (turns)", min_value=1, max_value=99, value=5, key="cond_duration")
        if st.button("➕ Apply Condition", use_container_width=True):
            gs['conditions'][new_cond] = CONDITION_EFFECTS[new_cond]['desc']
            st.session_state.condition_timers[new_cond] = duration
            st.success(f"Applied {new_cond} for {duration} turns!")
            time.sleep(0.5)
            st.rerun()
    
    with col_remove:
        st.markdown("**Remove Condition:**")
        if gs['conditions']:
            rem_cond = st.selectbox("Active Conditions", list(gs['conditions'].keys()), key="rem_cond")
            if st.button("➖ Remove Condition", use_container_width=True):
                del gs['conditions'][rem_cond]
                if rem_cond in st.session_state.condition_timers:
                    del st.session_state.condition_timers[rem_cond]
                st.success(f"Removed {rem_cond}!")
                time.sleep(0.5)
                st.rerun()
        else:
            st.info("No active conditions to remove.")

    # 3. SAVE / LOAD
    st.divider()
    st.subheader("💾 Game Persistence")
    col_save, col_load = st.columns(2)
    
    with col_save:
        save_data = json.dumps({
            'game_state': gs,
            'condition_timers': st.session_state.condition_timers
        }, indent=4)
        st.download_button(
            label="DOWNLOAD SAVE (.json)",
            data=save_data,
            file_name=f"vexal_save_{gs['name']}.json",
            mime="application/json",
            use_container_width=True
        )
        st.caption("Exports your current stats, inventory, and Vexal state.")

    with col_load:
        uploaded_file = st.file_uploader("UPLOAD SAVE (.json)", type=["json"], label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                save_obj = json.load(uploaded_file)
                if "game_state" in save_obj and "vaxel_state" in save_obj["game_state"]:
                    st.session_state.game_state = save_obj["game_state"]
                    if "condition_timers" in save_obj:
                        st.session_state.condition_timers = save_obj["condition_timers"]
                    st.success("Save Loaded! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid save file format.")
            except Exception as e:
                st.error(f"Error loading save: {e}")

    # 4. ACCESSIBILITY & RESET
    st.divider()
    col_acc, col_rst = st.columns(2)
    
    with col_acc:
        st.session_state.tts_enabled = st.toggle(
            "🔊 Text-to-Speech (HTML5)", 
            value=st.session_state.tts_enabled,
            help="Toggle automatic reading of GM responses."
        )

    with col_rst:
        if st.button("⚠️ RESET ADVENTURE", use_container_width=True, help="Permanently wipes current progress."):
            st.session_state.game_state = INITIAL_GAME_STATE.copy()
            st.session_state.messages = []
            st.session_state.condition_timers = {}
            st.rerun()
