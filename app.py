import streamlit as st
import re
import random
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

# --- 1. INITIALIZATION (The fix for your NameError) ---
st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True

# Shorthand for readability AFTER initialization
gs = st.session_state.game_state

# --- 2. CORE MECHANICS ---
def get_effective_attributes():
    eff = gs['attributes'].copy()
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA|ALL)', impact.upper())
        for val, attr in mods:
            if attr == 'ALL':
                for a in eff: eff[a] += int(val)
            else: eff[attr] += int(val)
    for slot in ['Head', 'Torso', 'Legs', 'Hands']:
        if slot in gs['equipment']:
            mat = gs['equipment'][slot]['material']
            penalty = MAT_PROPS.get(mat, {}).get('Dex_Penalty', 0)
            eff['DEX'] += penalty
    return eff

def apply_level_up(attr_choice, feat_choice):
    gs['level'] += 1
    gs['xp'] -= gs['xp_next']
    gs['xp_next'] = int(gs['xp_next'] * 1.5)
    gs['attributes'][attr_choice] += 1
    # Feat application logic here...
    st.session_state.messages.append({"role": "assistant", "content": f"✨ **LEVEL UP!** Reached Level {gs['level']}. Improved {attr_choice}."})

# --- 3. SIDEBAR (PERSISTENCE AUDIT: OK) ---
with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    def custom_bar(label, current, maximum, color):
        percent = min(100, max(0, (current / maximum) * 100))
        st.markdown(f'<div style="font-size:0.7rem; font-weight:bold;">{label} {int(current)}/{maximum}</div>', unsafe_allow_html=True)
        st.progress(percent/100)

    custom_bar("❤️ HP", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAM", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    custom_bar("⚖️ FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.divider()
    eff = get_effective_attributes()
    st.markdown("<div style='text-align:center; font-size:0.7rem; font-weight:bold;'>ATTRIBUTES</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff[attr]; diff = val - base
        color = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        cols[i%3].markdown(f"<div style='text-align:center; background:#1e1e1e; padding:5px; border-radius:4px;'><div style='font-size:0.55rem; color:#888;'>{attr}</div><div style='color:{color}; font-weight:bold; font-size:0.8rem;'>{val}</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"**Vaxel:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")

# --- 4. MAIN PAGE ---
# LEVEL UP MODAL (PERSISTENCE AUDIT: NEW FEATURE)
if gs['xp'] >= gs['xp_next']:
    with st.container(border=True):
        st.markdown("### 🌟 LEVEL UP AVAILABLE")
        c1, c2 = st.columns(2)
        attr_up = c1.selectbox("Attribute +1", list(gs['attributes'].keys()))
        feat_up = c2.selectbox("Select Feat", list(FEAT_LIBRARY.keys()))
        if st.button("Ascend"):
            apply_level_up(attr_up, feat_up)
            st.rerun()

tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_char:
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Skills"):
            sc1, sc2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()):
                (sc1 if i%2==0 else sc2).write(f"**{s}**: Rank {r}")
    st.divider()
    st.subheader("Spellbook")
    for sp in gs['known_spells']: st.caption(f"✨ {sp} ({gs['mana_costs'].get(sp)} MP)")

with tab_inv:
    st.subheader("Equipment")
    for slot, d in gs['equipment'].items(): st.write(f"**{slot}**: {d['item']} ({d['material']})")
    st.divider()
    st.write(f"💰 **Currency:** {gs['inventory']['currency']['Silver']} Silver")

with tab_sett:
    st.session_state.audio_enabled = st.toggle("Audio TTS", value=st.session_state.audio_enabled)
    if st.button("Undo Turn"):
        if len(st.session_state.messages) >= 2: st.session_state.messages = st.session_state.messages[:-2]; st.rerun()

with tab_con:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("---")
    # ACTION DECK (PERSISTENCE AUDIT: OK)
    d1, d2, d3 = st.columns(3)
    all_sks = [s for cat in gs['skills'].values() for s in cat.keys()]
    sk_sel = d1.selectbox("Skills", all_sks)
    if d1.button("💪 Use Skill"): st.session_state.cmd_buffer = f"I use {sk_sel} to "; st.rerun()
    
    sp_sel = d2.selectbox("Spells", gs['known_spells'])
    if d2.button("✨ Cast"): st.session_state.cmd_buffer = f"I cast {sp_sel} on "; st.rerun()
    
    imp_in = d3.text_input("Impromptu")
    if d3.button("🚀 Execute"):
        if imp_in: st.session_state.messages.append({"role": "user", "content": imp_in}); st.rerun()

    direct = st.chat_input("Command Amara...")
    if direct:
        st.session_state.messages.append({"role": "user", "content": st.session_state.cmd_buffer + direct})
        st.session_state.cmd_buffer = ""
        st.rerun()
