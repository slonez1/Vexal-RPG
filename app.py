import streamlit as st
import json
import time
from datetime import datetime

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

# --- SIDEBAR (Location, Time, Turn #, Vexal banner) ---
def _render_sidebar():
    with st.sidebar:
        st.title(f"🛡️ {gs.get('name', 'Unknown')}")
        # Prominent Vexal banner (increase importance of remaining notification)
        if gs.get('vexal_state', '').lower() == "active":
            st.markdown(f"<div class='vexal-banner'>VEXAL STATE: {gs.get('vexal_state', 'Active').upper()} — CORRUPTION ACTIVE</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='vexal-banner' style='background:#6c757d;'>VEXAL STATE: {gs.get('vexal_state','Unknown')}</div>", unsafe_allow_html=True)

        # Primary bars
        custom_bar("❤️ HEALTH", gs.get('hp', 0), cur_hp_m, "#ff4b4b")
        custom_bar("⚡ STAMINA", gs.get('stamina', 0), cur_sta_m, "#28a745")
        custom_bar("✨ MANA", gs.get('mana', 0), cur_mana_m, "#007bff")
        st.markdown("<hr style='border:1px solid #444;margin:12px 0;'>", unsafe_allow_html=True)
        custom_bar("⚖️ DIVINE FAVOR", gs.get('divine_favor', 0), 100, "#fd7e14")
        
        # Location / Time / Turn display
        st.markdown("**📍 Location**")
        st.write(gs.get('location', 'Unknown'))
        # Small description from lore if present
        loc_desc = lore.st.session_state.lore["locations"].get(gs.get('location', ''), {}).get('description', '')
        if loc_desc:
            st.caption(loc_desc)
        st.markdown("---")
        st.markdown(f"**⏱️ Time:** {st.session_state.get('last_action_time', '')}")
        st.markdown(f"**🔁 Turn #:** {st.session_state.get('turn_count', 0)}")

        # Active Conditions Display (hide severity for Vexal)
        if gs.get('conditions'):
            st.markdown("**Active Effects:**")
            for condition in gs['conditions'].keys():
                if condition in CONDITION_EFFECTS:
                    cond_data = CONDITION_EFFECTS[condition]
                    timer = st.session_state.condition_timers.get(condition, 0)
                    hide_sev = (condition == "Vexal Active")
                    render_condition_badge(condition, cond_data, timer, hide_severity=hide_sev)
        
        st.write("### Attributes")
        a_cols = st.columns(3)
        for i, (attr, base) in enumerate(gs['attributes'].items()):
            val = eff_attr.get(attr, base)
            diff = val - base
            clr = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
            sign = "+" if diff > 0 else ""
            a_cols[i%3].markdown(f"<div class='attr-box'><div class='attr-label'>{attr}</div><div class='attr-val' style='color:{clr};'>{val} ({sign}{diff})</div></div>", unsafe_allow_html=True)
        
        st.divider()
        custom_bar("💓 AROUSAL", gs.get('arousal', 0), 100, "#e83e8c")
        boxes = "".join(["▣" if i < gs.get('orgasm_count', 0) else "▢" for i in range(10)])
        st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)
        
        # Movement Speed Indicator
        if movement_speed != 1.0:
            speed_pct = int(movement_speed * 100)
            speed_color = "#28a745" if movement_speed > 1.0 else "#ff4b4b"
            st.markdown(f"**🏃 Movement:** <span style='color:{speed_color};'>{speed_pct}%</span>", unsafe_allow_html=True)

_render_sidebar()

# --- TABS (add LORE tab) ---
tab_con, tab_stat, tab_char, tab_inv, tab_lore, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "📚 LORE", "⚙️ SETTINGS"])

with tab_stat:
    # (existing Status content remains unchanged) ...
    # [ unchanged code omitted here for brevity — keep same as previous version up to Experience display ]
    st.subheader("📊 Experience")
    exp = gs.get("experience", 0)
    exp_next = gs.get("experience_next", 100)
    exp_progress = min(1.0, exp / max(1, exp_next))
    st.progress(exp_progress)
    st.write(f"Experience: {exp} / {exp_next}")
    # (rest of the Status tab unchanged)

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
                # increment turn count and update time
                st.session_state.turn_count = st.session_state.get('turn_count', 0) + 1
                st.session_state.last_action_time = datetime.utcnow().isoformat()
                st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        full = st.session_state.cmd_buffer + direct
        st.session_state.messages.append({"role": "user", "content": full})
        st.session_state.cmd_buffer = ""
        res = get_gm_response(full)
        st.session_state.messages.append({"role": "assistant", "content": res})
        trigger_tts(res)
        # increment turn count and update time
        st.session_state.turn_count = st.session_state.get('turn_count', 0) + 1
        st.session_state.last_action_time = datetime.utcnow().isoformat()
        st.rerun()

with tab_char:
    st.subheader("Amara Silvermoon — Character Sheet")
    col_left, col_right = st.columns([1,2])
    with col_left:
        # Portrait uploader / display
        portrait = st.session_state.get("portrait")
        uploaded = st.file_uploader("Upload Portrait (use the supplied Amara image)", type=["png","jpg","jpeg"], key="portrait_upload")
        if uploaded is not None:
            st.session_state.portrait = uploaded
            portrait = uploaded
        if portrait:
            st.image(portrait, caption=gs.get('name','Amara'), use_column_width=True)
        else:
            st.image("https://via.placeholder.com/240x320.png?text=Portrait", caption="No portrait uploaded", use_column_width=True)

    with col_right:
        st.markdown(f"**Name:** {gs.get('name','Amara Silvermoon')}")
        st.markdown(f"**Level:** {gs.get('level',1)}  |  **Experience:** {gs.get('experience',0)} / {gs.get('experience_next',100)}")
        st.markdown(f"**Divine Favor:** {gs.get('divine_favor',0)}")
        st.markdown("**Attributes:**")
        attr_cols = st.columns(3)
        for i,(k,v) in enumerate(gs.get('attributes', {}).items()):
            attr_cols[i%3].metric(label=k, value=v)
        st.markdown("**Skills & Mastery:**")
        for cat, sks in gs.get('skills', {}).items():
            with st.expander(f"{cat}"):
                for s, r in sks.items():
                    exp = gs.get("skills_exp", {}).get(cat, {}).get(s, 0)
                    lvl = exp // 10
                    st.write(f"- **{s}**: Rank {r} (Skill Level {lvl})")
        st.markdown("**Spellbook:**")
        for spn in gs.get('known_spells', []):
            base_cost = gs.get('mana_costs', {}).get(spn, 0)
            effective_cost = int(base_cost * spell_cost_multiplier)
            st.write(f"- {spn} ({effective_cost} MP)")

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

with tab_lore:
    st.subheader("📚 Lore & Knowledge Repository")
    lore.init_lore()
    # Vexal Lore
    with st.expander("1. Vexal Lore (Main Quest)"):
        st.write(st.session_state.lore["vexal"]["main_quest"])
        st.markdown("Notes:")
        for n in st.session_state.lore["vexal"]["notes"]:
            st.write(f"- {n}")
        new_note = st.text_input("Add Vexal Note", key="add_vex_note")
        if st.button("➕ Add Vexal Note"):
            if new_note:
                lore.add_vexal_note(new_note)
                st.success("Added note.")
                st.rerun()

    # Persons of Interest
    with st.expander("2. Persons of Interest"):
        if not st.session_state.lore["persons"]:
            st.info("No persons recorded yet.")
        else:
            for name, info in st.session_state.lore["persons"].items():
                with st.container():
                    st.markdown(f"**{name}** — {info.get('role','')}")
                    if info.get('significance'):
                        st.caption(info['significance'])
                    for note in info.get('notes', []):
                        st.write(f"- {note}")
        pname = st.text_input("Add Person Name", key="add_person_name")
        prole = st.text_input("Role / Title", key="add_person_role")
        pnote = st.text_input("Note", key="add_person_note")
        if st.button("➕ Add Person"):
            if pname:
                lore.add_person(pname, role=prole, note=pnote)
                st.success("Person added.")
                st.rerun()

    # Locations
    with st.expander("3. Locations"):
        if not st.session_state.lore["locations"]:
            st.info("No locations recorded yet.")
        else:
            for loc, data in st.session_state.lore["locations"].items():
                st.markdown(f"**{loc}** — {data.get('description','')}")
                st.caption(f"Discovered at turn {data.get('discovered_at_turn','?')}")
        lname = st.text_input("Add Location Name", key="add_loc_name")
        ldesc = st.text_input("Short Description", key="add_loc_desc")
        if st.button("➕ Add Location"):
            if lname:
                lore.add_location(lname, description=ldesc)
                st.success("Location added.")
                st.rerun()

with tab_sett:
    st.subheader("🛠️ System Controls")
    # (settings content remains unchanged from prior)
    if st.button("⬅️ UNDO LAST TURN", use_container_width=True, help="Reverts the last player action and GM response."):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
        else:
            st.warning("No turns left to undo!")
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
    st.divider()
    st.subheader("💾 Game Persistence")
    col_save, col_load = st.columns(2)
    with col_save:
        save_data = json.dumps({
            'game_state': gs,
            'condition_timers': st.session_state.condition_timers,
            'lore': st.session_state.get('lore', {})
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
                if "game_state" in save_obj and "vexal_state" in save_obj["game_state"]:
                    st.session_state.game_state = save_obj["game_state"]
                    if "condition_timers" in save_obj:
                        st.session_state.condition_timers = save_obj["condition_timers"]
                    if "lore" in save_obj:
                        st.session_state.lore = save_obj["lore"]
                    st.success("Save Loaded! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid save file format. Required key 'vexal_state' missing.")
            except Exception as e:
                st.error(f"Error loading save: {e}")
    st.divider()
    col_acc, col_rst = st.columns(2)
    with col_acc:
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
            st.session_state.lore = {}
            st.session_state.turn_count = 0
            st.rerun()
