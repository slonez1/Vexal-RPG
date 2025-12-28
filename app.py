import streamlit as st
import json
import re
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- INITIALIZATION ---
if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""

gs = st.session_state.game_state

# --- ATTRIBUTE ENGINE ---
def get_effective_attributes():
    eff = gs['attributes'].copy()
    for slot, data in gs['equipment'].items():
        if data.get('type') == 'Armor':
            eff['DEX'] += MAT_PROPS.get(data['material'], {}).get('Dex_Penalty', 0)
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA|ALL)', impact.upper())
        for val, attr in mods:
            if attr == 'ALL':
                for a in eff: eff[a] += int(val)
            else: eff[attr] += int(val)
    return eff

# Detect changes for Console Notifications
current_eff = get_effective_attributes()
if gs.get('prev_eff') and gs['prev_eff'] != current_eff:
    for attr in gs['attributes']:
        diff = current_eff[attr] - gs['prev_eff'].get(attr, current_eff[attr])
        if diff != 0:
            st.toast(f"Attribute Changed: {attr} {'+' if diff > 0 else ''}{diff}", icon="⚠️")
gs['prev_eff'] = current_eff

# --- SIDEBAR (IMMUTABLE INFRASTRUCTURE) ---
def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.sidebar.markdown(f"<div style='font-size:0.7rem; font-weight:bold;'>{label} {int(current)}/{maximum}</div>", unsafe_allow_html=True)
    st.sidebar.progress(percent/100)

with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    custom_bar("❤️ HP", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    st.markdown("<hr style='border:1px solid #444;'>", unsafe_allow_html=True)
    custom_bar("⚖️ FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.write("### Attributes")
    cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = current_eff[attr]
        diff = val - base
        color = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        cols[i%3].markdown(f"<div style='text-align:center; background:#1e1e1e; padding:5px; border-radius:4px; border:1px solid #333;'><div style='font-size:0.5rem; color:#888;'>{attr}</div><div style='color:{color}; font-weight:bold;'>{val}({diff})</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"**Vaxel:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

# LEVEL UP MODAL (Inside Console)
if gs['xp'] >= gs['xp_next']:
    with tab_con:
        with st.expander("🌟 LEVEL UP AVAILABLE!", expanded=True):
            st.write("Increase your power. Choose carefully:")
            l1, l2, l3 = st.columns(3)
            new_attr = l1.selectbox("Attribute +1", list(gs['attributes'].keys()))
            
            flat_skills = []
            for cat, s_list in gs['skills'].items():
                for s in s_list: flat_skills.append(f"{cat}: {s}")
            new_skill = l2.selectbox("Skill +2", flat_skills)
            
            new_feat = l3.selectbox("Select Feat", list(FEAT_LIBRARY.keys()))
            st.info(f"**Feat Info:** {FEAT_LIBRARY[new_feat]['desc']}")
            
            if st.button("Ascend Amara"):
                gs['level'] += 1
                gs['xp'] -= gs['xp_next']
                gs['xp_next'] = int(gs['xp_next'] * 1.5)
                gs['attributes'][new_attr] += 1
                cat, skname = new_skill.split(": ")
                gs['skills'][cat][skname] += 2
                gs['feats'].append(new_feat)
                st.rerun()

with tab_con:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        s_list = [s for cat in gs['skills'].values() for s in cat.keys()]
        sk = st.selectbox("Skills", s_list, label_visibility="collapsed")
        if st.button("💪 Use Skill"): st.session_state.cmd_buffer = f"[Use Skill: {sk}] "; st.rerun()
    with c2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Use Spell"): st.session_state.cmd_buffer = f"[Use Spell: {sp}] "; st.rerun()
    with c3:
        imp = st.text_input("Impromptu", label_visibility="collapsed", placeholder="Craft action...")
        if st.button("🚀 Execute"):
            st.session_state.messages.append({"role": "user", "content": f"🛠️ [IMPROMPTU]: {imp}"})
            st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        final = st.session_state.cmd_buffer + direct
        st.session_state.messages.append({"role": "user", "content": final})
        st.session_state.cmd_buffer = ""
        st.rerun()

with tab_inv:
    st.subheader("Equipped Items")
    for slot, d in gs['equipment'].items():
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2,1,1])
            col_a.markdown(f"**{slot}:** {d['item']} ({d['material']})")
            if d.get('type') == 'Armor':
                props = MAT_PROPS.get(d['material'], {})
                col_b.write(f"🛡️ DT: {props.get('DT')} | 🔊 Noise: {props.get('Noise')}")
            elif d.get('type') == 'Weapon':
                col_b.write(f"⚔️ Dmg: {d.get('dmg')}")
            col_c.progress(d['cond']/100, text=f"Cond: {d['cond']}%")

with tab_sett:
    col_s1, col_s2 = st.columns(2)
    if col_s1.button("💾 Save Game", use_container_width=True):
        st.download_button("Download Save", json.dumps(gs), "save.json")
    if col_s2.button("📂 Load Game", use_container_width=True):
        uploaded = st.file_uploader("Upload save.json")
        if uploaded:
            st.session_state.game_state = json.load(uploaded)
            st.rerun()

#
