import streamlit as st
import re
import random
from data import INITIAL_GAME_STATE, MAT_PROPS, FEATS

st.set_page_config(page_title="Vexal Engine v5", layout="wide")

# --- SESSION INITIALIZATION ---
if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True

gs = st.session_state.game_state

# --- MECHANICS ENGINE ---
def get_effective_attributes():
    eff = gs['attributes'].copy()
    # 1. Apply Condition Modifiers
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA|ALL)', impact.upper())
        for val, attr in mods:
            if attr == 'ALL':
                for a in eff: eff[a] += int(val)
            else: eff[attr] += int(val)
    # 2. Apply Armor Penalties
    for slot in ['Head', 'Torso', 'Legs', 'Hands']:
        if slot in gs['equipment']:
            mat = gs['equipment'][slot]['material']
            penalty = MAT_PROPS.get(mat, {}).get('Dex_Penalty', 0)
            eff['DEX'] += penalty
    return eff

def get_saving_throw(attr_name):
    eff = get_effective_attributes()
    # Saving Throw = Attribute + (Level / 2)
    return eff[attr_name] + (gs['level'] // 2)

def calculate_attack():
    weapon = gs['equipment']['MainHand']
    eff = get_effective_attributes()
    scaling_stat = weapon.get('scaling', 'STR')
    stat_mod = (eff[scaling_stat] - 10) // 2
    
    roll = random.randint(1, 20)
    # Find skill rank (checking Martial category)
    skill_rank = gs['skills']['Martial'].get(weapon['type'], 0)
    
    to_hit = roll + stat_mod + (skill_rank // 2)
    
    d_num, d_sides = map(int, weapon['dmg'].split('d'))
    dmg = sum(random.randint(1, d_sides) for _ in range(d_num)) + stat_mod
    return to_hit, dmg, roll

# --- UI COMPONENTS ---
def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.7rem; font-weight: bold;">
                <span>{label}</span><span>{int(current)}/{maximum}</span>
            </div>
            <div style="background-color: #333; height: 8px; width: 100%; border-radius: 4px;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🛡️ {gs['name']}")
    custom_bar("❤️ HP", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAM", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    st.markdown("<hr style='margin:10px 0; border-color:#444;'>", unsafe_allow_html=True)
    custom_bar("⚖️ FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    eff = get_effective_attributes()
    st.write("### Attributes")
    cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff[attr]
        diff = val - base
        color = "#28a745" if diff > 0 else "#ff4b4b" if diff < 0 else "#eee"
        cols[i%3].markdown(f"<div style='text-align:center; background:#111; padding:5px; border-radius:5px;'><div style='font-size:0.6rem; color:#888;'>{attr}</div><div style='color:{color}; font-weight:bold;'>{val}</div></div>", unsafe_allow_html=True)

    st.divider()
    st.progress(gs['xp'] / gs['xp_next'], text=f"XP: {gs['xp']}/{gs['xp_next']}")
    if st.button("🌟 Level Up Available!") if gs['xp'] >= gs['xp_next'] else None:
        st.toast("Level Up logic triggered!")

# --- MAIN TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_stat:
    st.subheader("Active Conditions")
    for c, desc in gs['conditions'].items():
        st.error(f"**{c}**: {desc}")
    st.divider()
    st.subheader("Saving Throws")
    s_cols = st.columns(3)
    for i, attr in enumerate(['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']):
        s_cols[i%3].metric(f"{attr} Save", get_saving_throw(attr))

with tab_char:
    st.subheader("Character Sheet")
    for cat, skills in gs['skills'].items():
        with st.expander(f"{cat} Skills"):
            for s, r in skills.items():
                st.write(f"**{s}**: Rank {r}")

with tab_sett:
    st.subheader("Engine Settings")
    st.session_state.audio_enabled = st.toggle("Enable TTS Voice", value=st.session_state.audio_enabled)
    if st.button("Reset Game State"):
        del st.session_state.game_state
        st.rerun()

with tab_con:
    chat_win = st.container(height=400)
    with chat_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    st.write("---")
    # THE RESTORED ACTION DECK
    c1, c2, c3 = st.columns(3)
    with c1:
        all_skills = [s for cat in gs['skills'].values() for s in cat.keys()]
        sel_sk = st.selectbox("Skills", all_skills)
        if st.button("💪 Use Skill"): 
            st.session_state.cmd_buffer = f"I use my {sel_sk} skill to "
            st.rerun()
    with c2:
        sel_sp = st.selectbox("Spells", gs['known_spells'])
        if st.button("✨ Cast Spell"):
            st.session_state.cmd_buffer = f"I cast {sel_sp} on "
            st.rerun()
    with c3:
        imp = st.text_input("Impromptu")
        if st.button("🚀 Execute"):
            st.session_state.messages.append({"role": "user", "content": f"Impromptu: {imp}"})
            st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct or (st.session_state.cmd_buffer and st.button("Confirm Staged Action")):
        final = st.session_state.cmd_buffer + (direct if direct else "")
        st.session_state.messages.append({"role": "user", "content": final})
        st.session_state.cmd_buffer = ""
        # GM Trigger logic here
        st.rerun()
