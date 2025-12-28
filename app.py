import streamlit as st
import json
import re
import time
from data import INITIAL_GAME_STATE, MAT_PROPS, FEAT_LIBRARY

st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

# --- CSS & TTS HOOKS ---
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

# --- GM AI ENGINE (RESTORED) ---
def get_gm_response(prompt):
    # Simulated GM Narrative Logic - This would connect to your LLM API
    narrative = f"The GM observes your action: {prompt}. Your stats (STR:{eff_attr['STR']} / WIS:{eff_attr['WIS']}) suggest a deliberate effort..."
    return narrative

def trigger_tts(text):
    if st.session_state.tts_enabled:
        st.components.v1.html(f"<script>window.parent.speak('{text.replace("'", "\\'")}');</script>", height=0)

# --- MATH ENGINE (CORRECTED VEXAL) ---
def get_effective_stats():
    eff_attr = gs['attributes'].copy()
    pool_mod = 0
    if "Vexal Active" in gs['conditions']:
        pool_mod = -20
        for a in eff_attr: eff_attr[a] -= 2
    for slot, data in gs['equipment'].items():
        if data.get('type') == 'Armor':
            eff_attr['DEX'] += MAT_PROPS.get(data['material'], {}).get('Dex_Penalty', 0)
    return eff_attr, pool_mod

eff_attr, p_mod = get_effective_stats()
cur_hp_m, cur_sta_m, cur_mana_m = gs['hp_max']+p_mod, gs['stamina_max']+p_mod, gs['mana_max']+p_mod

# --- SIDEBAR (IMMUTABLE UI) ---
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
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** <span style='color:#e83e8c;'>{boxes}</span>", unsafe_allow_html=True)

# --- TABS ---
tab_con, tab_stat, tab_char, tab_inv, tab_sett = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "⚙️ SETTINGS"])

with tab_con:
    # Notification & Interaction Layer
    last_msg = st.session_state.messages[-1]['content'] if st.session_state.messages else ""
    if "[SKILL TRAINER]" in last_msg:
        with st.expander("🎓 TRAINER", expanded=True):
            s_all = [s for cat in gs['skills'].values() for s in cat.keys()]
            t_sk = st.selectbox("Select Skill (+1 Rank / 50 Silv)", s_all)
            if st.button("Train") and gs['inventory']['currency']['Silver'] >= 50:
                gs['inventory']['currency']['Silver'] -= 50
                for c in gs['skills']: 
                    if t_sk in gs['skills'][c]: gs['skills'][c][t_sk] += 1
                st.rerun()

    c_win = st.container(height=350)
    with c_win:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    st.divider()
    # ACTION DECK (RE-STABILIZED)
    d1, d2, d3 = st.columns(3)
    with d1:
        sk = st.selectbox("Skills", [s for cat in gs['skills'].values() for s in cat.keys()], label_visibility="collapsed")
        if st.button("💪 Add Skill Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Skill: {sk}] "; st.rerun()
    with d2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Add Spell Tag", use_container_width=True): 
            st.session_state.cmd_buffer = f"[Use Spell: {sp}] "; st.rerun()
    with d3:
        imp = st.text_input("Impromptu", placeholder="Craft Custom Action...", label_visibility="collapsed")
        if st.button("🚀 Execute", use_container_width=True):
            if imp:
                full_imp = f"🛠️ [IMPROMPTU]: {imp}"
                st.session_state.messages.append({"role": "user", "content": full_imp})
                gm_reply = get_gm_response(full_imp)
                st.session_state.messages.append({"role": "assistant", "content": gm_reply})
                trigger_tts(gm_reply); st.rerun()

    direct = st.chat_input("Command...")
    if direct:
        full_msg = st.session_state.cmd_buffer + direct
        st.session_state.messages.append({"role": "user", "content": full_msg})
        st.session_state.cmd_buffer = ""
        gm_reply = get_gm_response(full_msg)
        st.session_state.messages.append({"role": "assistant", "content": gm_reply})
        trigger_tts(gm_reply); st.rerun()

with tab_stat:
    for c, d in gs['conditions'].items(): st.warning(f"**{c}**: {d}")
    st.divider()
    sc = st.columns(3)
    for i, a in enumerate(['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']):
        sc[i%3].metric(f"{a} Save", eff_attr[a] + (gs['level'] // 2))

with tab_char:
    for cat, sks in gs['skills'].items():
        with st.expander(f"{cat} Mastery"):
            cc1, cc2 = st.columns(2)
            for i, (s, r) in enumerate(sks.items()): (cc1 if i%2==0 else cc2).write(f"**{s}**: Rank {r}")
    st.divider(); st.subheader("✨ Spellbook")
    spc1, spc2 = st.columns(2)
    for i, spn in enumerate(gs['known_spells']):
        (spc1 if i%2==0 else spc2).info(f"**{spn}** ({gs['mana_costs'].get(spn)} MP)")

with tab_inv:
    for slot, d in gs['equipment'].items():
        with st.container(border=True):
            st.write(f"**{slot}:** {d['item']} ({d['material']})")
            st.progress(d['cond']/100)
    st.write(f"💰 Silver: {gs['inventory']['currency']['Silver']}")

with tab_sett:
    st.session_state.tts_enabled = st.toggle("🔊 Text-to-Speech", value=st.session_state.tts_enabled)
    if st.button("⬅️ UNDO TURN", use_container_width=True):
        if len(st.session_state.messages) >= 2: st.session_state.messages = st.session_state.messages[:-2]; st.rerun()
    if st.button("⚠️ RESET ADVENTURE", use_container_width=True):
        st.session_state.game_state = INITIAL_GAME_STATE.copy(); st.session_state.messages = []; st.rerun()
    st.divider()
    s1, s2 = st.columns(2)
    s1.download_button("💾 Export Save", json.dumps(gs), "save.json")
    up = s2.file_uploader("📂 Import Save", type=["json"])
    if up: st.session_state.game_state = json.load(up); st.rerun()
