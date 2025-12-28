import streamlit as st
import json
import re
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
    </style>
    <script>
        function speak(text) {
            const msg = new SpeechSynthesisUtterance(text);
            window.speechSynthesis.speak(msg);
        }
    </script>
""", unsafe_allow_html=True)

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
if "tts_enabled" not in st.session_state: st.session_state.tts_enabled = True

gs = st.session_state.game_state

# --- GM AI & TTS ---
def get_gm_response(prompt):
    return f"Narrative: Amara acts upon '{prompt}'. (Vexal influence detected)."

def trigger_tts(text):
    if st.session_state.tts_enabled:
        st.components.v1.html(f"<script>window.parent.speak('{text.replace("'", "\\'")}');</script>", height=0)

# --- MATH ENGINE: FIXED DEX CALCULATION ---
def get_effective_stats():
    eff_attr = gs['attributes'].copy() # Always start from base attributes
    pool_mod = 0
    if "Vexal Active" in gs['conditions']:
        pool_mod = -20
        for a in eff_attr: eff_attr[a] -= 2
    
    # Apply Armor DEX Penalties ONCE
    for slot in ['Head', 'Torso', 'Legs', 'Hands', 'OffHand']:
        if slot in gs['equipment'] and gs['equipment'][slot].get('type') == 'Armor':
            mat = gs['equipment'][slot]['material']
            eff_attr['DEX'] += MAT_PROPS.get(mat, {}).get('Dex_Penalty', 0)
    return eff_attr, pool_mod

eff_attr, p_mod = get_effective_stats()
cur_hp_m, cur_sta_m, cur_mana_m = gs['hp_max']+p_mod, gs['stamina_max']+p_mod, gs['mana_max']+p_mod

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
    
    st.write("### Attributes")
    a_cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff_attr[attr]; diff = val - base
        clr = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        a_cols[i%3].markdown(f"<div class='attr-box'><div class='attr-label'>{attr}</div><div class='attr-val' style='color:{clr};'>{val}({diff})</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"**Vaxel:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_stat:
    # 1. Condition Overview
    st.subheader("🩹 Active Conditions")
    if not gs['conditions']:
        st.info("Amara is currently free of any debilitating conditions.")
    else:
        for condition, effect in gs['conditions'].items():
            # Use warning style for negative conditions
            st.warning(f"**{condition}**: {effect}")

    st.divider()

    # 2. Saving Throws Logic
    # Formula: (Effective Attribute) + (Level // 2)
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
        # Calculate save based on the effective attributes (which already include Vexal/Armor penalties)
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
        # Visualizing the Subjugation risk
        st.markdown(f"**Subjugation Peak:** `{gs['orgasm_count']}/10` overflows")
        peak_progress = (gs['orgasm_count'] / 10)
        st.progress(peak_progress)
        if gs['orgasm_count'] >= 7:
            st.error("⚠️ HIGH RISK: Vexal state nearing Subjugation threshold.")
        else:
            st.success("Vexal state currently manageable.")

    # 4. Resistances (If applicable)
    st.divider()
    st.subheader("🛡️ Resistances")
    r_col1, r_col2, r_col3 = st.columns(3)
    r_col1.write("**Holy:** 25%")
    r_col2.write("**Void:** -10%")
    r_col3.write("**Physical:** 5%")
    
with tab_con:
    c_win = st.container(height=350)
    with c_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        sk_list = sorted([s for cat in gs['skills'].values() for s in cat.keys()])
        sk = st.selectbox("Skills", sk_list, label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sk}] "; st.rerun()
    with d2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Spell: {sp}] "; st.rerun()
    with d3:
        imp = st.text_input("Impromptu", placeholder="Action...", label_visibility="collapsed")
        if st.button("🚀 Execute", use_container_width=True):
            if imp:
                full = f"🛠️ [IMPROMPTU]: {imp}"
                st.session_state.messages.append({"role": "user", "content": full})
                res = get_gm_response(full); st.session_state.messages.append({"role": "assistant", "content": res})
                trigger_tts(res); st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        full = st.session_state.cmd_buffer + direct
        st.session_state.messages.append({"role": "user", "content": full})
        st.session_state.cmd_buffer = ""
        res = get_gm_response(full); st.session_state.messages.append({"role": "assistant", "content": res})
        trigger_tts(res); st.rerun()

with tab_char:
    st.subheader("Mastered Skills")
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Mastery"):
            c1, c2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): (c1 if i%2==0 else c2).write(f"**{s}**: {r}")
    st.divider(); st.subheader("✨ Spellbook")
    sp1, sp2 = st.columns(2)
    for i, spn in enumerate(gs['known_spells']):
        (sp1 if i%2==0 else sp2).info(f"**{spn}** ({gs['mana_costs'].get(spn)} MP)")

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
    
    # 1. UNDO TURN (Logic Integrity)
    if st.button("⬅️ UNDO LAST TURN", use_container_width=True, help="Reverts the last player action and GM response."):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
        else:
            st.toast("No turns left to undo!", icon="🚫")

    # 2. SAVE / LOAD (The Missing Persistence Logic)
    st.divider()
    st.subheader("💾 Game Persistence")
    col_save, col_load = st.columns(2)
    
    with col_save:
        # Serializes current game_state into a JSON file for download
        save_data = json.dumps(gs, indent=4)
        st.download_button(
            label="DOWNLOAD SAVE (.json)",
            data=save_data,
            file_name=f"vexal_save_{gs['name']}.json",
            mime="application/json",
            use_container_width=True
        )
        st.caption("Exports your current stats, inventory, and Vexal state.")

    with col_load:
        # Handles the file upload and updates the session state
        uploaded_file = st.file_uploader("UPLOAD SAVE (.json)", type=["json"], label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                new_state = json.load(uploaded_file)
                # Validation check: Ensure it's a valid Vexal save
                if "vaxel_state" in new_state and "attributes" in new_state:
                    st.session_state.game_state = new_state
                    st.success("Save Loaded! Refreshing...")
                    time.sleep(1) # Visual feedback before rerun
                    st.rerun()
                else:
                    st.error("Invalid save file format.")
            except Exception as e:
                st.error(f"Error loading save: {e}")

    # 3. ACCESSIBILITY & RESET (TTS Persistence)
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
            st.rerun()
