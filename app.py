import streamlit as st
import json
import re
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- 1. STATE & PERSISTENCE ---
if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""

gs = st.session_state.game_state

# --- 2. MATH ENGINE (VEXAL CORRECTION) ---
def get_effective_stats():
    eff_attr = gs['attributes'].copy()
    pool_mod = 0
    
    # Apply Vexal & Conditions
    if "Vexal Active" in gs['conditions']:
        pool_mod = -20
        for a in eff_attr: eff_attr[a] -= 2
        
    # Apply Armor DEX Penalties
    for slot, data in gs['equipment'].items():
        if data.get('type') == 'Armor':
            eff_attr['DEX'] += MAT_PROPS.get(data['material'], {}).get('Dex_Penalty', 0)
            
    return eff_attr, pool_mod

eff_attr, p_mod = get_effective_stats()
cur_hp_max, cur_sta_max, cur_mana_max = gs['hp_max'] + p_mod, gs['stamina_max'] + p_mod, gs['mana_max'] + p_mod

# --- 3. SIDEBAR (IMMUTABLE UI) ---
def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.sidebar.markdown(f"<div style='font-size:0.75rem; font-weight:bold;'>{label} {int(current)}/{maximum}</div>", unsafe_allow_html=True)
    st.sidebar.progress(percent/100)

with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    custom_bar("❤️ HEALTH", gs['hp'], cur_hp_max, "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], cur_sta_max, "#28a745")
    custom_bar("✨ MANA", gs['mana'], cur_mana_max, "#007bff")
    st.markdown("<hr style='border: 1px solid #444;'>", unsafe_allow_html=True)
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.write("### Attributes")
    a_cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff_attr[attr]
        diff = val - base
        color = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        a_cols[i%3].markdown(f"<div style='text-align:center; background:#1e1e1e; padding:5px; border-radius:4px; border:1px solid #333;'><div style='font-size:0.55rem; color:#888;'>{attr}</div><div style='color:{color}; font-weight:bold;'>{val}({diff})</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"**Vaxel:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.sidebar.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- 4. TABS & INTERACTION ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_con:
    # --- GM NOTIFICATION LISTENER ---
    last_msg = st.session_state.messages[-1]['content'] if st.session_state.messages else ""
    
    if "[SKILL TRAINER]" in last_msg:
        with st.expander("🎓 TRAINER AVAILABLE", expanded=True):
            st.write("Spend 50 Silver to increase a skill by +1.")
            all_sks = [s for cat in gs['skills'].values() for s in cat.keys()]
            target_sk = st.selectbox("Select Skill", all_sks)
            if st.button("Train Skill") and gs['inventory']['currency']['Silver'] >= 50:
                gs['inventory']['currency']['Silver'] -= 50
                for cat in gs['skills']: 
                    if target_sk in gs['skills'][cat]: gs['skills'][cat][target_sk] += 1
                st.success(f"Trained {target_sk}!"); st.rerun()

    if "[TRADESMAN]" in last_msg:
        with st.expander("⚒️ TRADESMAN AVAILABLE", expanded=True):
            repair_target = st.selectbox("Item to Repair (20 Silver)", list(gs['equipment'].keys()))
            if st.button("Repair Item") and gs['inventory']['currency']['Silver'] >= 20:
                gs['inventory']['currency']['Silver'] -= 20
                gs['equipment'][repair_target]['cond'] = 100
                st.rerun()

    # --- CONSOLE UI ---
    chat_win = st.container(height=350)
    with chat_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        sk_sel = st.selectbox("Skills", [s for cat in gs['skills'].values() for s in cat.keys()], label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): st.session_state.cmd_buffer = f"[Use Skill: {sk_sel}] "; st.rerun()
    with d2:
        sp_sel = st.selectbox("Spells", gs.get('known_spells', []), label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True): st.session_state.cmd_buffer = f"[Use Spell: {sp_sel}] "; st.rerun()
    with d3:
        imp = st.text_input("Impromptu", placeholder="Craft...", label_visibility="collapsed")
        if st.button("🚀 Execute", use_container_width=True):
            if imp: st.session_state.messages.append({"role": "user", "content": f"🛠️ [IMPROMPTU]: {imp}"}); st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        st.session_state.messages.append({"role": "user", "content": st.session_state.cmd_buffer + direct})
        st.session_state.cmd_buffer = ""
        st.rerun()

with tab_stat:
    st.subheader("Active Conditions")
    for c, d in gs['conditions'].items(): st.warning(f"**{c}**: {d}")
    st.divider()
    st.subheader("Saving Throws (Attribute + Level/2)")
    sc = st.columns(3)
    for i, a in enumerate(['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']):
        sc[i%3].metric(f"{a} Save", eff_attr[a] + (gs['level'] // 2))

with tab_char:
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Mastery"):
            cc1, cc2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): (cc1 if i%2==0 else cc2).write(f"**{s}**: Rank {r}")

with tab_inv:
    st.subheader("Equipped Gear")
    for slot, d in gs['equipment'].items():
        with st.container(border=True):
            i1, i2, i3 = st.columns([2,1,1])
            i1.write(f"**{slot}:** {d['item']} ({d['material']})")
            i3.progress(d['cond']/100, text=f"{d['cond']}%")
    st.write(f"💰 Silver: {gs['inventory']['currency']['Silver']}")

with tab_sett:
    if st.button("⬅️ UNDO TURN", use_container_width=True):
        if len(st.session_state.messages) >= 2: 
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
    if st.button("⚠️ RESET ADVENTURE", use_container_width=True):
        st.session_state.game_state = INITIAL_GAME_STATE.copy()
        st.session_state.messages = []
        st.rerun()
    st.divider()
    s1, s2 = st.columns(2)
    s1.download_button("💾 Save to File", json.dumps(gs), "save.json")
    uploaded = s2.file_uploader("📂 Load from File", type=["json"])
    if uploaded:
        st.session_state.game_state = json.load(uploaded); st.rerun()
