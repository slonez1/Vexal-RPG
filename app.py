import streamlit as st
import json
import time

# Local modules
from data import INITIAL_GAME_STATE, MAT_PROPS
from game_state import (
    init_session_state,
    update_condition_timers,
    get_effective_stats,
    get_gs_copy
)
from ui_components import custom_bar, render_condition_badge
from gm_ai import get_gm_response, trigger_tts
from conditions import CONDITION_EFFECTS

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

# --- SESSION INIT (preserve existing keys) ---
init_session_state()
gs = st.session_state.game_state

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
spell_cost_multiplier = stats['spell_cost_multiplier']
movement_speed = stats['movement_speed']
mana_regen = stats['mana_regen']

cur_hp_m = gs.get('hp_max', 0) + p_mod + hp_max_penalty
cur_sta_m = gs.get('stamina_max', 0) + p_mod
cur_mana_m = gs.get('mana_max', 0) + p_mod

# Apply stamina drain (preserve original behaviour)
gs['stamina'] = max(0, gs.get('stamina', 0) - stamina_drain)

# --- SIDEBAR (IMMUTABLE) ---
def _render_sidebar():
    with st.sidebar:
        st.title(f"🛡️ {gs.get('name', 'Unknown')}")
        custom_bar("❤️ HEALTH", gs.get('hp', 0), cur_hp_m, "#ff4b4b")
        custom_bar("⚡ STAMINA", gs.get('stamina', 0), cur_sta_m, "#28a745")
        custom_bar("✨ MANA", gs.get('mana', 0), cur_mana_m, "#007bff")
        st.markdown("<hr style='border:1px solid #444;margin:15px 0;'>", unsafe_allow_html=True)
        custom_bar("⚖️ DIVINE FAVOR", gs.get('divine_favor', 0), 100, "#fd7e14")
        
        # Active Conditions Display
        if gs.get('conditions'):
            st.markdown("**Active Effects:**")
            for condition in gs['conditions'].keys():
                if condition in CONDITION_EFFECTS:
                    cond_data = CONDITION_EFFECTS[condition]
                    timer = st.session_state.condition_timers.get(condition, 0)
                    render_condition_badge(condition, cond_data, timer)
        
        st.write("### Attributes")
        a_cols = st.columns(3)
        for i, (attr, base) in enumerate(gs['attributes'].items()):
            val = eff_attr.get(attr, base)
            diff = val - base
            clr = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
            sign = "+" if diff > 0 else ""
            a_cols[i%3].markdown(f"<div class='attr-box'><div class='attr-label'>{attr}</div><div class='attr-val' style='color:{clr};'>{val} ({sign}{diff})</div></div>", unsafe_allow_html=True)
        
        st.divider()
        # Display the correctly-named key 'vexal_state' (safe-get)
        st.markdown(f"**Vexal:** `{gs.get('vexal_state', gs.get('vaxel_state', 'Unknown'))}`")
        custom_bar("💓 AROUSAL", gs.get('arousal', 0), 100, "#e83e8c")
        boxes = "".join(["▣" if i < gs.get('orgasm_count', 0) else "▢" for i in range(10)])
        st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)
        
        # Movement Speed Indicator
        if movement_speed != 1.0:
            speed_pct = int(movement_speed * 100)
            speed_color = "#28a745" if movement_speed > 1.0 else "#ff4b4b"
            st.markdown(f"**🏃 Movement:** <span style='color:{speed_color};'>{speed_pct}%</span>", unsafe_allow_html=True)

_render_sidebar()

# --- TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_stat:
    # 1. Condition Overview
    st.subheader("🩹 Active Conditions")
    if not gs.get('conditions'):
        st.info("Amara is currently free of any debilitating conditions.")
    else:
        for condition in gs['conditions'].keys():
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
                st.warning(f"**{condition}**: {gs['conditions'].get(condition, '')}")

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

    level_bonus = gs.get('level', 0) // 2
    for i, (save_name, attr_key, hint) in enumerate(save_list):
        total_save = eff_attr.get(attr_key, gs['attributes'].get(attr_key, 0)) + level_bonus
        with save_cols[i % 3]:
            st.metric(
                label=save_name, 
                value=f"+{total_save}", 
                delta=f"Attr: {eff_attr.get(attr_key, gs['attributes'].get(attr_key, 0))} | Lvl: {level_bonus}",
                delta_color="off",
                help=hint
            )

    # 3. Vexal State Mechanics
    st.subheader("🧬 Vexal Influence Breakdown")
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        st.markdown("**Attribute Suppression:**")
        st.code("-2 to all Base Attributes (Applied)", language="diff")
        st.markdown("**Pool Suppression:**")
        st.code("-20 Max HP\n-20 Max Stamina\n-20 Max Mana", language="diff")

    with v_col2:
        st.markdown(f"**Subjugation Peak:** `{gs.get('orgasm_count', 0)}/10` overflows")
        peak_progress = (gs.get('orgasm_count', 0) / 10)
        st.progress(peak_progress)
        if gs.get('orgasm_count', 0) >= 7:
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

    # 6. Skill Progression Display
    st.divider()
    st.subheader("📈 Skill Progression")
    for cat, sks in gs.get('skills', {}).items():
        with st.expander(f"{cat} Mastery"):
            c1, c2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()):
                exp = gs.get("skills_exp", {}).get(cat, {}).get(s, 0)
                level = exp // 10
                progress = exp % 10
                c1.write(f"**{s}**: {r} (Level {level}, {progress}/10 exp)")
                c2.write(f"Exp: {exp}")
    
    # 7. Experience Display
    st.divider()
    st.subheader("📊 Experience")
    st.progress(gs.get("experience", 0) / 100)
    st.write(f"Experience: {gs.get('experience', 0)} / 100")
    
    # 8. Location System
    st.divider()
    st.subheader("📍 Location")
    if "location" not in gs:
        gs["location"] = "Dark Forest"
    st.markdown(f"**Current Location:** {gs['location']}")
    
    # 9. Stat Tracking Charts
    st.divider()
    st.subheader("📈 Stat Tracking")
    st.line_chart({
        "HP": [gs.get('hp', 0), gs.get('hp_max', 0)],
        "Stamina": [gs.get('stamina', 0), gs.get('stamina_max', 0)],
        "Mana": [gs.get('mana', 0), gs.get('mana_max', 0)]
    })
    
    # 10. Puzzle System
    st.divider()
    st.subheader("🧩 Puzzles")
    if "puzzle" not in gs:
        gs["puzzle"] = "none"
    if gs["puzzle"] == "none":
        st.info("No puzzles active. Look for clues in the environment.")
    else:
        st.warning(f"Puzzle: {gs['puzzle']} - Try to solve it!")
        if st.button("Solve Puzzle"):
            gs["puzzle"] = "none"
            st.success("Puzzle solved! You found a hidden passage.")
            st.rerun()

with tab_con:
    c_win = st.container()
    with c_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): 
                st.markdown(m["content"])
    
    st.write("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        sk_list = sorted([s for cat in gs.get('skills', {}).values() for s in cat.keys()])
        sk = st.selectbox("Skills", sk_list, label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sk}] "
            st.rerun()
    with d2:
        sp = st.selectbox("Spells", gs.get('known_spells', []), label_visibility="collapsed")
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
    for cat, sks in gs.get('skills', {}).items():
        with st.expander(f"{cat} Mastery"):
            c1, c2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): 
                (c1 if i%2==0 else c2).write(f"**{s}**: {r}")
    
    st.divider()
    st.subheader("✨ Spellbook")
    sp1, sp2 = st.columns(2)
    for i, spn in enumerate(gs.get('known_spells', [])):
        base_cost = gs.get('mana_costs', {}).get(spn, 0)
        effective_cost = int(base_cost * spell_cost_multiplier)
        cost_display = f"{effective_cost} MP"
        if effective_cost != base_cost:
            cost_display += f" (base: {base_cost})"
        (sp1 if i%2==0 else sp2).info(f"**{spn}** ({cost_display})")

with tab_inv:
    st.subheader("Equipment Detail")
    for slot, d in gs.get('equipment', {}).items():
        with st.container():
            props = MAT_PROPS.get(d.get('material', ''), {})
            st.markdown(f"**Slot:** `{slot}` | **Item:** {d.get('item', '')} | **Material:** {d.get('material', '')}")
            col_a, col_b, col_c = st.columns(3)
            col_a.write(f"🛡️ AC (DT): {props.get('DT', 'N/A')}")
            col_b.write(f"⚖️ Weight: {props.get('Weight', '0')} lbs")
            col_c.write(f"🔊 Noise: {props.get('Noise', '0')}")
            st.progress(d.get('cond', 0)/100)
            st.caption(f"Condition: {d.get('cond', 0)}%")

with tab_sett:
    st.subheader("🛠️ System Controls")
    
    # 1. UNDO TURN
    if st.button("⬅️ UNDO LAST TURN", use_container_width=True, help="Reverts the last player action and GM response."):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
        else:
            st.warning("No turns left to undo!")

    # 2. CONDITION MANAGEMENT
    st.divider()
    st.subheader("🩹 Condition Manager")
    
    col_add, col_remove = st.columns(2)
    
    with col_add:
        st.markdown("**Add Condition:**")
        new_cond = st.selectbox("Select Condition", list(CONDITION_EFFECTS.keys()), key="add_cond")
        duration = st.number_input("Duration (turns)", min_value=1, max_value=99, value=5, key="cond_duration")
        if st.button("➕ Apply Condition", use_container_width=True):
            gs.setdefault('conditions', {})[new_cond] = CONDITION_EFFECTS[new_cond]['desc']
            st.session_state.condition_timers[new_cond] = duration
            st.success(f"Applied {new_cond} for {duration} turns!")
            time.sleep(0.5)
            st.rerun()
    
    with col_remove:
        st.markdown("**Remove Condition:**")
        if gs.get('conditions'):
            rem_cond = st.selectbox("Active Conditions", list(gs['conditions'].keys()), key="rem_cond")
            if st.button("➖ Remove Condition", use_container_width=True):
                if rem_cond in gs.get('conditions', {}):
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
            file_name=f"vexal_save_{gs.get('name','save')}.json",
            mime="application/json",
            use_container_width=True
        )
        st.caption("Exports your current stats, inventory, and Vexal state.")

    with col_load:
        uploaded_file = st.file_uploader("UPLOAD SAVE (.json)", type=["json"], label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                save_obj = json.load(uploaded_file)
                # require the correctly-named key 'vexal_state' in game_state for this repo
                if "game_state" in save_obj and "vexal_state" in save_obj["game_state"]:
                    st.session_state.game_state = save_obj["game_state"]
                    if "condition_timers" in save_obj:
                        st.session_state.condition_timers = save_obj["condition_timers"]
                    st.success("Save Loaded! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid save file format. Required key 'vexal_state' missing.")
            except Exception as e:
                st.error(f"Error loading save: {e}")

    # 4. ACCESSIBILITY & RESET
    st.divider()
    col_acc, col_rst = st.columns(2)
    
    with col_acc:
        # Use checkbox (widely supported) instead of toggle to control TTS
        st.session_state.tts_enabled = st.checkbox(
            "🔊 Text-to-Speech (HTML5)", 
            value=st.session_state.get("tts_enabled", True),
            help="Toggle automatic reading of GM responses."
        )

    with col_rst:
        if st.button("⚠️ RESET ADVENTURE", use_container_width=True, help="Permanently wipes current progress."):
            st.session_state.game_state = INITIAL_GAME_STATE.copy()
            st.session_state.messages = []
            st.session_state.condition_timers = {}
            st.rerun()
