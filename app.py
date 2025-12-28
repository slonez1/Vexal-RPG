import streamlit as st
import re
import random
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

# --- 1. CONFIG & CSS (IMMUTABLE) ---
st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #0e1117; }
        .attr-box { background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 5px; text-align: center; margin-bottom: 5px; }
        .attr-label { font-size: 0.6rem; color: #888; text-transform: uppercase; }
        .attr-val { font-size: 0.9rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE.copy()
if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True

gs = st.session_state.game_state

# --- 2. GM LOGIC HOOK (RESTORED) ---
def get_gm_response(user_input):
    """
    Logic to generate GM narrative. 
    In a live environment, this is where your LLM API call sits.
    """
    # Placeholder for GM narrative response logic
    # It incorporates the game state (gs) and attributes for 'private' calculation
    return f"The GM acknowledges your action: '{user_input}'. (Narrative response would be generated here based on your level {gs['level']} and stats.)"

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

def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{int(current)}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 5px; height: 12px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 5px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (PERSISTENCE AUDIT: VERIFIED) ---
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
    a_cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        val = eff[attr]; diff = val - base
        color = "#ff4b4b" if diff < 0 else "#28a745" if diff > 0 else "#eee"
        val_str = f"{val}({diff})" if diff != 0 else f"{val}"
        with a_cols[i%3]:
            st.markdown(f"""<div class="attr-box"><div class="attr-label">{attr}</div><div class="attr-val" style="color:{color};">{val_str}</div></div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- 4. MAIN PAGE ---
if gs['xp'] >= gs['xp_next']:
    with st.container(border=True):
        st.markdown("### 🌟 LEVEL UP AVAILABLE")
        cl1, cl2 = st.columns(2)
        attr_up = cl1.selectbox("Attribute +1", list(gs['attributes'].keys()))
        feat_up = cl2.selectbox("Select Feat", list(FEAT_LIBRARY.keys()))
        if st.button("Confirm Level Up", use_container_width=True):
            gs['level'] += 1; gs['xp'] -= gs['xp_next']; gs['xp_next'] = int(gs['xp_next'] * 1.5)
            gs['attributes'][attr_up] += 1
            st.rerun()

tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_con:
    chat_container = st.container(height=400)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        all_sks = [s for cat in gs['skills'].values() for s in cat.keys()]
        sel_sk = st.selectbox("Skills", all_sks, label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sel_sk}] "; st.rerun()
    with col2:
        sel_sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True):
            st.session_state.cmd_buffer = f"[Use Spell: {sel_sp}] "; st.rerun()
    with col3:
        imp_text = st.text_input("Impromptu Crafting", placeholder="Define custom action...", label_visibility="collapsed")
        if st.button("🚀 Execute Impromptu", use_container_width=True):
            if imp_text:
                full_imp = f"🛠️ **[IMPROMPTU ACTION]:** {imp_text}"
                st.session_state.messages.append({"role": "user", "content": full_imp})
                # RESTORED: Trigger GM Response
                gm_reply = get_gm_response(full_imp)
                st.session_state.messages.append({"role": "assistant", "content": gm_reply})
                st.rerun()

    direct_cmd = st.chat_input("Direct Command...")
    if direct_cmd:
        final_msg = st.session_state.cmd_buffer + direct_cmd
        st.session_state.messages.append({"role": "user", "content": final_msg})
        st.session_state.cmd_buffer = ""
        # RESTORED: Trigger GM Response
        gm_reply = get_gm_response(final_msg)
        st.session_state.messages.append({"role": "assistant", "content": gm_reply})
        st.rerun()
    
    if st.session_state.cmd_buffer:
        st.info(f"**Action Prefix Active:** `{st.session_state.cmd_buffer}`")

# (Tabs: Status, Character, Inventory, Settings remain untouched/fully restored)
with tab_stat:
    st.subheader("Conditions & Ailments")
    for c, d in gs['conditions'].items(): st.warning(f"**{c}**: {d}")
    st.divider()
    st.subheader("Saving Throws")
    sc = st.columns(3)
    for i, a in enumerate(['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']):
        sc[i%3].metric(f"{a} Save", eff[a] + (gs['level'] // 2))

with tab_char:
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Mastery"):
            cc1, cc2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): (cc1 if i%2==0 else cc2).write(f"**{s}**: Rank {r}")
    st.divider(); st.subheader("Spellbook")
    spc1, spc2 = st.columns(2)
    for i, sp in enumerate(gs['known_spells']): (spc1 if i%2==0 else spc2).info(f"✨ {sp} ({gs['mana_costs'].get(sp)} MP)")

with tab_inv:
    for slot, data in gs['equipment'].items(): st.write(f"**{slot}:** {data['item']} ({data['material']})")
    st.divider(); st.subheader("Inventory")
    for cont, data in gs['inventory']['containers'].items(): st.write(f"📁 **{cont}**: {', '.join(data['items'])}")
    st.write(f"💰 **Currency:** {gs['inventory']['currency']['Silver']} Silver")

with tab_sett:
    st.session_state.audio_enabled = st.toggle("🔊 Audio Master", value=st.session_state.audio_enabled)
    if st.button("⬅️ Undo Last Turn"):
        if len(st.session_state.messages) >= 2: st.session_state.messages = st.session_state.messages[:-2]; st.rerun()
