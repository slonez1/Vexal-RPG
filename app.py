import streamlit as st
import re
import random
import base64
from data import INITIAL_GAME_STATE, MAT_PROPS

# --- 1. CONFIG ---
st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True

gs = st.session_state.game_state

# --- 2. LOGIC ENGINE ---
def get_effective_attributes():
    eff = gs['attributes'].copy()
    # Apply Condition Penalties
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA|ALL)', impact.upper())
        for val, attr in mods:
            if attr == 'ALL':
                for a in eff: eff[a] += int(val)
            else: eff[attr] += int(val)
    # Apply Armor DEX Penalties
    for slot in ['Head', 'Torso', 'Legs', 'Hands']:
        if slot in gs['equipment']:
            mat = gs['equipment'][slot]['material']
            penalty = MAT_PROPS.get(mat, {}).get('Dex_Penalty', 0)
            eff['DEX'] += penalty
    return eff

def get_saving_throw(attr):
    eff = get_effective_attributes()
    return eff[attr] + (gs['level'] // 2)

# --- 3. UI HELPERS ---
def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{int(current)}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR (RESTORED FULL) ---
with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    custom_bar("❤️ HEALTH", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    st.markdown("<hr style='border: 1px solid #444; margin: 15px 0;'>", unsafe_allow_html=True)
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.divider()
    eff = get_effective_attributes()
    st.markdown("<div style='text-align:center; font-size:0.7rem; font-weight:bold; color:#888;'>ATTRIBUTES</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff[attr]; diff = val - base
        color = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        val_str = f"{val}({diff})" if diff != 0 else f"{val}"
        cols[i%3].markdown(f"<div style='text-align:center; background:#1e1e1e; border:1px solid #333; border-radius:4px; padding:5px;'><div style='font-size:0.6rem; color:#888;'>{attr}</div><div style='font-size:0.9rem; font-weight:bold; color:{color};'>{val_str}</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")

# --- 5. TABS (RESTORED FULL) ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_stat:
    st.subheader("Active Conditions")
    if not gs['conditions']: st.write("No active ailments.")
    for c, d in gs['conditions'].items(): st.warning(f"**{c}**: {d}")
    st.divider()
    st.subheader("Saving Throws")
    s_cols = st.columns(3)
    for i, a in enumerate(['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']):
        s_cols[i%3].metric(f"{a} Save", get_saving_throw(a))

with tab_char:
    st.subheader("Character Sheet")
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Skills"):
            c1, c2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()):
                (c1 if i%2==0 else c2).write(f"**{s}**: Rank {r}")
    st.divider()
    st.subheader("Spellbook")
    sp_cols = st.columns(2)
    for i, sp in enumerate(gs['known_spells']):
        sp_cols[i%2].info(f"✨ {sp} ({gs['mana_costs'].get(sp)} MP)")

with tab_inv:
    st.subheader("Equipped Gear")
    for slot, data in gs['equipment'].items():
        st.write(f"**{slot}:** {data['item']} ({data['material']}) — `{data['cond']}%` Condition")
    st.divider()
    st.subheader("Inventory Storage")
    for cont, data in gs['inventory']['containers'].items():
        st.write(f"📁 **{cont}**: {', '.join(data['items']) if data['items'] else 'Empty'}")
    st.write(f"💰 **Currency:** {gs['inventory']['currency']['Silver']} Silver")

with tab_sett:
    st.session_state.audio_enabled = st.toggle("🔊 Audio Enabled", value=st.session_state.audio_enabled)
    if st.button("⬅️ Undo Last Turn"):
        if len(st.session_state.messages) >= 2: st.session_state.messages = st.session_state.messages[:-2]
        st.rerun()
    if st.button("⚠️ Hard Reset"):
        st.session_state.game_state = INITIAL_GAME_STATE
        st.session_state.messages = []
        st.rerun()

with tab_con:
    chat_win = st.container(height=400)
    with chat_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    # ACTION DECK
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        all_sk = [s for cat in gs['skills'].values() for s in cat.keys()]
        sk = st.selectbox("Skills", all_sk)
        if st.button("💪 Use Skill"): st.session_state.cmd_buffer = f"I use {sk} to "; st.rerun()
    with c2:
        sp = st.selectbox("Spells", gs['known_spells'])
        if st.button("✨ Cast"): st.session_state.cmd_buffer = f"I cast {sp} on "; st.rerun()
    with c3:
        imp = st.text_input("Impromptu", placeholder="Magic...")
        if st.button("🚀 Execute"):
            if imp: st.session_state.messages.append({"role": "user", "content": f"Impromptu: {imp}"}); st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct or (st.session_state.cmd_buffer and st.button("Confirm Staged Action")):
        final = (st.session_state.cmd_buffer + (direct if direct else "")).strip()
        st.session_state.messages.append({"role": "user", "content": final})
        st.session_state.cmd_buffer = ""
        st.rerun()
