import streamlit as st
import json
import re
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- CSS FOR UI INTEGRITY ---
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

gs = st.session_state.game_state

# --- LOGIC ENGINE ---
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
            else:
                if attr in eff: eff[attr] += int(val)
    return eff

def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.sidebar.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{int(current)}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 5px; height: 12px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 5px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR (RESTORED COLORS & GRID) ---
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
        with a_cols[i%3]:
            st.markdown(f"""<div class="attr-box"><div class="attr-label">{attr}</div><div class="attr-val" style="color:{color};">{val}({diff})</div></div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- MAIN TABS (RESTORED ALL) ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_con:
    chat_win = st.container(height=400)
    with chat_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        s_list = [s for cat in gs['skills'].values() for s in cat.keys()]
        sk = st.selectbox("Skills", s_list, label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sk}] "; st.rerun()
    with col2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True):
            st.session_state.cmd_buffer = f"[Use Spell: {sp}] "; st.rerun()
    with col3:
        imp = st.text_input("Impromptu", placeholder="Craft...", label_visibility="collapsed")
        if st.button("🚀 Execute", use_container_width=True):
            if imp: st.session_state.messages.append({"role": "user", "content": f"🛠️ [IMPROMPTU]: {imp}"}); st.rerun()

    direct = st.chat_input("Direct Command...")
    if direct:
        st.session_state.messages.append({"role": "user", "content": st.session_state.cmd_buffer + direct})
        st.session_state.cmd_buffer = ""
        st.rerun()

with tab_stat:
    st.subheader("Conditions")
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
    st.divider()
    st.subheader("Spellbook")
    spc1, spc2 = st.columns(2)
    for i, sp in enumerate(gs['known_spells']): (spc1 if i%2==0 else spc2).info(f"✨ {sp} ({gs['mana_costs'].get(sp)} MP)")

with tab_inv:
    st.subheader("Equipped Gear")
    for slot, d in gs['equipment'].items():
        with st.container(border=True):
            i1, i2, i3 = st.columns([2,1,1])
            i1.write(f"**{slot}:** {d['item']} ({d['material']})")
            if d.get('type') == 'Armor':
                p = MAT_PROPS.get(d['material'], {})
                i2.write(f"🛡️ DT: {p.get('DT')} | 🔊 Noise: {p.get('Noise')}")
            i3.progress(d['cond']/100, text=f"{d['cond']}%")
    st.write(f"💰 Silver: {gs['inventory']['currency']['Silver']}")

with tab_sett:
    if st.button("⬅️ Undo Turn"):
        if len(st.session_state.messages) >= 2: st.session_state.messages = st.session_state.messages[:-2]; st.rerun()
    st.divider()
    s1, s2 = st.columns(2)
    s1.download_button("💾 Export Save", json.dumps(gs), "save.json")
    uploaded = s2.file_uploader("📂 Import Save", type=["json"])
    if uploaded:
        st.session_state.game_state = json.load(uploaded); st.rerun()
