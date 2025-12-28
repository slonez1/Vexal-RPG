import streamlit as st
import re
import json
import base64
import time
from google import genai
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. CONFIGURATION & INITIALIZATION ---
st.set_page_config(page_title="Vexal Engine v5", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_clients():
    try:
        gcp_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(gcp_info)
        client_tts = texttospeech.TextToSpeechClient(credentials=creds)
        client_gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        return client_tts, client_gemini
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None, None

client_tts, client_gemini = init_clients()

# --- 2. DATA CONSTANTS ---
SKILL_MAP = {
    "One-Handed": "STR", "Two-Handed": "STR", "Bladed": "DEX", "Blunt": "STR",
    "Daggers": "DEX", "Axes": "STR", "Polearms": "STR", "Marksmanship": "DEX",
    "Blocking": "STR", "Heavy Armor": "CON", "Light Armor": "DEX", "Unarmed": "STR",
    "Holy": "WIS", "Arcane": "INT", "Elemental": "INT", "Illusion": "CHA",
    "Death": "INT", "Blood": "CHA", "Restoration": "WIS", "Void Navigation": "INT",
    "Stealth": "DEX", "Lockpicking": "DEX", "Pickpocket": "DEX",
    "Poisoning": "INT", "Trap Disarming": "DEX", "Shadow-Stitch": "INT",
    "Alchemy": "INT", "Blacksmithing": "STR", "Enchanting": "INT", "Survival": "WIS",
    "Athletics": "STR", "Acrobatics": "DEX", "Anatomy": "INT", "Tinkering": "INT",
    "Cooking": "WIS", "Leatherworking": "DEX",
    "Persuasion": "CHA", "Intimidation": "CHA", "Deception": "CHA",
    "Insight": "WIS", "Performance": "CHA", "Etiquette": "CHA", "Bartering": "CHA"
}

SKILL_CATS = {
    "Martial": ["One-Handed", "Two-Handed", "Bladed", "Blunt", "Daggers", "Axes", "Polearms", "Marksmanship", "Blocking", "Heavy Armor", "Light Armor", "Unarmed"],
    "Mystical": ["Holy", "Arcane", "Elemental", "Illusion", "Death", "Blood", "Restoration", "Void Navigation"],
    "Subterfuge": ["Stealth", "Lockpicking", "Pickpocket", "Poisoning", "Trap Disarming", "Shadow-Stitch"],
    "Professional": ["Alchemy", "Blacksmithing", "Enchanting", "Survival", "Athletics", "Acrobatics", "Anatomy", "Tinkering", "Cooking", "Leatherworking"],
    "Social": ["Persuasion", "Intimidation", "Deception", "Insight", "Performance", "Etiquette", "Bartering"]
}

SYSTEM_RULES = "You are a GM for a dark fantasy RPG. Use tags like [PLAYER DAMAGE: 10], [AROUSAL: +5], [CONDITION: Name | Effect]."

# --- 3. SESSION STATE ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'hp': 250, 'hp_max': 250, 'stamina': 180, 'stamina_max': 180,
        'mana': 200, 'mana_max': 200, 'divine_favor': 95, 'arousal': 0, 'orgasm_count': 0,
        'turn_counter': 0, 'vaxel_state': "Active",
        'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
        'skills': {skill: 10 for skill in SKILL_MAP.keys()}, # Initialize all at Rank 10
        'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
        'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
        'conditions': {"Vexal Active": "(-2 to STR, -2 DEX, -2 CON, -2 INT, -2 WIS, -2 CHA)"},
        'equipment': {'Torso': {'item': 'Plate', 'material': 'Steel'}},
        'inventory': {'containers': {'Belt Pouch': {'capacity': 5, 'items': ['Key']}}, 'currency': {'Silver': 150}},
        'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Current Objective": "Enter the Spire."}}
    }

if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""

# --- 4. UTILITY FUNCTIONS ---
def get_effective_attributes():
    gs = st.session_state.game_state
    eff = gs['attributes'].copy()
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA)', impact.upper())
        for val, attr in mods: eff[attr] += int(val)
    return eff

def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{current}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 5px; height: 12px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 5px; transition: width 0.5s;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def parse_logic(text):
    gs = st.session_state.game_state
    gs['turn_counter'] += 1
    dmg = re.search(r'\[PLAYER DAMAGE: (\d+)\]', text)
    if dmg: gs['hp'] = max(0, gs['hp'] - int(dmg.group(1)))
    
    aro = re.search(r'\[AROUSAL: \+(\d+)\]', text)
    if aro:
        gs['arousal'] += int(aro.group(1))
        if gs['arousal'] >= 100:
            gs['arousal'] = 0
            gs['orgasm_count'] += 1
            gs['conditions']["Orgasm Aftershock"] = "(-4 STR, -4 DEX for 5 turns)"
            st.toast("VAXEL OVERLOAD!", icon="🔥")

    cond = re.search(r'\[CONDITION: (.*?) \| (.*?)\]', text)
    if cond: gs['conditions'][cond.group(1)] = cond.group(2)

# --- 5. SIDEBAR ---
with st.sidebar:
    gs = st.session_state.game_state
    st.title("🛡️ AMARA")
    
    custom_bar("❤️ HEALTH", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    
    # Requirement 1: Horizontal line between Mana and Divine Favor
    st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #444;'>", unsafe_allow_html=True)
    
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.divider()
    
    # Requirement 2: Fancy Attribute Grid with Modifier Logic
    eff = get_effective_attributes()
    st.markdown("<div style='text-align:center; font-size:0.8rem; font-weight:bold; color:#aaa; margin-bottom:10px;'>ATTRIBUTES</div>", unsafe_allow_html=True)
    
    attr_html = "<div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;'>"
    for attr, base_val in gs['attributes'].items():
        current_val = eff[attr]
        diff = current_val - base_val
        color = "#fff"
        display_val = f"{current_val}"
        
        if diff < 0:
            color = "#ff4b4b"
            display_val = f"{current_val}<span style='font-size:0.7rem;'>({diff})</span>"
        elif diff > 0:
            color = "#28a745"
            display_val = f"{current_val}<span style='font-size:0.7rem;'>(+{diff})</span>"
            
        attr_html += f"""
            <div style='background: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #333;'>
                <div style='font-size: 0.65rem; color: #888;'>{attr}</div>
                <div style='font-size: 1.1rem; font-weight: bold; color: {color};'>{display_val}</div>
            </div>
        """
    attr_html += "</div>"
    st.markdown(attr_html, unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")

# --- 6. UI TABS ---
tab_console, tab_status, tab_char, tab_inv, tab_lore = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE"])

with tab_status:
    st.subheader("Current Ailments & Buffs")
    for cond, effect in gs['conditions'].items():
        st.warning(f"**{cond}**: {effect}")

with tab_char:
    # Requirement 3: Categorized Skills
    st.subheader("Skills & Mastery")
    
    for cat, skills in SKILL_CATS.items():
        with st.expander(f"{cat} Skills", expanded=(cat=="Martial")):
            cols = st.columns(2)
            for idx, skill in enumerate(skills):
                rank = gs['skills'].get(skill, 0)
                primary_stat = SKILL_MAP.get(skill, "???")
                cols[idx % 2].markdown(f"**{skill}**: `Rank {rank}` <small>({primary_stat})</small>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Spellbook")
    for spell in gs['known_spells']:
        st.info(f"✨ {spell} — Cost: {gs['mana_costs'].get(spell, '??')} MP")

with tab_inv:
    st.subheader("Equipped Gear")
    for slot, data in gs['equipment'].items():
        st.write(f"**{slot}:** {data['item']} ({data['material']})")

with tab_lore:
    st.success(f"**Main Quest:** {gs['lore_ledger']['Main Quest']['Current Objective']}")

with tab_console:
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sk = st.selectbox("Skills", list(SKILL_MAP.keys()), label_visibility="collapsed")
        if st.button("💪 Use Skill", use_container_width=True):
            st.session_state.cmd_buffer = f"I use my {sk} skill to "
            st.rerun()
            
    with col2:
        sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Cast Spell", use_container_width=True):
            st.session_state.cmd_buffer = f"I cast {sp} on "
            st.rerun()
            
    with col3:
        impromptu_text = st.text_input("Impromptu Magic", placeholder="Divine essence...", label_visibility="collapsed")
        if st.button("🚀 Impromptu", use_container_width=True):
            if impromptu_text:
                st.session_state.messages.append({"role": "user", "content": f"I attempt an impromptu magical feat: {impromptu_text}"})
                st.rerun()

    direct_cmd = st.chat_input("Direct Command Amara...")
    final_action = st.session_state.cmd_buffer if st.session_state.cmd_buffer else direct_cmd
    
    if direct_cmd or (st.session_state.cmd_buffer and st.button("Confirm Staged Action")):
        st.session_state.messages.append({"role": "user", "content": final_action})
        st.session_state.cmd_buffer = ""
        ai_resp = f"The GM acknowledges your action: {final_action}. [PLAYER DAMAGE: 5]"
        parse_logic(ai_resp)
        st.session_state.messages.append({"role": "assistant", "content": ai_resp})
        st.rerun()
