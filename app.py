import streamlit as st
import re
import random
import base64
from google import genai
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. CONFIGURATION ---
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

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2}
}

# --- 3. SESSION STATE (YOUR FULL PC DATA) ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'name': 'Amara Silvermoon', 'level': 10,
        'hp': 100, 'hp_max': 250, 'mana': 30, 'mana_max': 200, 'stamina': 100, 'stamina_max': 180,
        'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95,
        'vaxel_state': "Active", 'turn_counter': 0,
        'conditions': {"Vexal Active": "(-2 STR, -2 DEX, -2 CON, -2 INT, -2 WIS, -2 CHA)"},
        'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
        'skills': {
            'Martial': {'One-Handed': 10, 'Two-Handed': 4, 'Bladed': 7, 'Blunt': 4, 'Blocking': 5, 'Heavy Armor': 8, 'Light Armor': 3, 'Unarmed': 1, 'Marksmanship': 3, 'Polearms': 2, 'Axes': 1},
            'Mystical': {'Holy': 10, 'Arcane': 4, 'Elemental': 3, 'Restoration': 7},
            'Professional': {'Alchemy': 2, 'Enchanting': 4, 'Survival': 4, 'Athletics': 6, 'Anatomy': 3, 'Cooking': 1, 'Blacksmithing': 4},
            'Social': {'Persuasion': 3, 'Intimidation': 3, 'Insight': 10, 'Etiquette': 7, 'Bartering': 1},
            'Subterfuge': {'Stealth': 2, 'Insight': 3}
        },
        'equipment': {
            'Head': {'item': 'Blessed Circlet', 'material': 'Gold-Filigree', 'cond': 100},
            'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel', 'cond': 85},
            'Legs': {'item': 'Plated Greaves', 'material': 'Steel', 'cond': 90},
            'Hands': {'item': 'Steel Gauntlets', 'material': 'Steel', 'cond': 90},
            'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Bladed', 'dmg': '2d8'},
            'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80}
        },
        'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Consecrate Ground', 'Lesser Smite', 'Lesser Heal', 'Purify Flesh'],
        'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Consecrate Ground': 20, 'Lesser Smite': 10, 'Lesser Heal': 12, 'Purify Flesh': 10},
        'inventory': {
            'containers': {
                'Belt Pouch': {'capacity': 5, 'items': ['Whetstone', 'Silver Key']},
                'Satchel': {'capacity': 15, 'items': ['Dried Rations', 'Holy Oil', 'Bandages']},
                'Scabbard': {'capacity': 1, 'items': []}
            },
            'currency': {'Silver': 150}
        },
        'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Current Objective": "Enter the Spire."}}
    }

if "messages" not in st.session_state: st.session_state.messages = []
if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""

# --- 4. ENGINE FUNCTIONS ---
def get_effective_attributes():
    gs = st.session_state.game_state
    eff = gs['attributes'].copy()
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA)', impact.upper())
        for val, attr in mods: eff[attr] += int(val)
    return eff

def calculate_total_dt():
    gs = st.session_state.game_state
    total_dt = 0
    armor_slots = ['Head', 'Torso', 'Legs', 'Hands', 'OffHand']
    for slot in armor_slots:
        if slot in gs['equipment']:
            item = gs['equipment'][slot]
            base_dt = MAT_PROPS.get(item['material'], {}).get('DT', 0)
            # Condition penalty: lose 1 DT for every 25% damage
            condition_mod = item['cond'] / 100
            total_dt += base_dt * condition_mod
    return round(total_dt, 1)

def combat_roll():
    gs = st.session_state.game_state
    weapon = gs['equipment']['MainHand']
    eff = get_effective_attributes()
    
    # Hit: d20 + DEX mod + (Skill/2)
    roll = random.randint(1, 20)
    skill_rank = gs['skills']['Martial'].get(weapon['type'], 0)
    hit_score = roll + ((eff['DEX']-10)//2) + (skill_rank // 2)
    
    # Damage: weapon dice + STR mod
    d_num, d_sides = map(int, weapon['dmg'].split('d'))
    dmg_roll = sum(random.randint(1, d_sides) for _ in range(d_num))
    total_dmg = dmg_roll + ((eff['STR']-10)//2)
    
    return hit_score, total_dmg, roll

def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{int(current)}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 4px; transition: width 0.5s;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    gs = st.session_state.game_state
    st.title(f"🛡️ {gs['name']}")
    st.caption(f"Level {gs['level']} Knight-Commander")
    
    custom_bar("❤️ HEALTH", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    
    # Requirement 1: Horizontal Line
    st.markdown("<hr style='border: 1px solid #444; margin: 15px 0;'>", unsafe_allow_html=True)
    
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.divider()
    
    # Requirement 2: Fancy Attribute Grid
    eff = get_effective_attributes()
    st.markdown("<div style='text-align:center; font-size:0.7rem; font-weight:bold; color:#888;'>ATTRIBUTES</div>", unsafe_allow_html=True)
    
    # Building the grid with Streamlit columns for stability
    cols = st.columns(3)
    for i, (attr, base) in enumerate(gs['attributes'].items()):
        current = eff[attr]
        diff = current - base
        with cols[i % 3]:
            color = "#fff"
            val_str = f"{current}"
            if diff < 0:
                color = "#ff4b4b"; val_str = f"{current}({diff})"
            elif diff > 0:
                color = "#28a745"; val_str = f"{current}(+{diff})"
            
            st.markdown(f"""
                <div style="background: #1e1e1e; border: 1px solid #333; padding: 5px; border-radius: 4px; text-align: center; margin-bottom:5px;">
                    <div style="font-size: 0.6rem; color: #888;">{attr}</div>
                    <div style="font-size: 0.9rem; font-weight: bold; color: {color};">{val_str}</div>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    dt = calculate_total_dt()
    st.metric("Total Damage Threshold (DT)", f"{dt}")
    
    custom_bar("💓 AROUSAL", gs['arousal'], 100, "#e83e8c")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Vaxel State:** `{gs['vaxel_state']}`")
    st.markdown(f"**Subjugation Peak:** `{boxes}`")

# --- 6. UI TABS ---
tab_console, tab_status, tab_char, tab_inv = st.tabs(["📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY"])

with tab_char:
    # Requirement 3: Categorized Skills
    st.subheader("Skills & Mastery")
    for cat, skills in gs['skills'].items():
        with st.expander(f"{cat} Skills"):
            c1, c2 = st.columns(2)
            for i, (sk, rank) in enumerate(skills.items()):
                stat = SKILL_MAP.get(sk, "???")
                (c1 if i%2==0 else c2).markdown(f"**{sk}**: `{rank}` <small>({stat})</small>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Spellbook")
    cols = st.columns(2)
    for i, spell in enumerate(gs['known_spells']):
        cols[i%2].info(f"✨ {spell} ({gs['mana_costs'].get(spell)} MP)")

with tab_inv:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Equipped")
        for slot, d in gs['equipment'].items():
            st.write(f"**{slot}:** {d['item']} ({d['material']}) — `{d['cond']}%` Condition")
    with col_b:
        st.subheader("Storage")
        for cont, d in gs['inventory']['containers'].items():
            st.write(f"**{cont}**: {', '.join(d['items'])}")
        st.write(f"**Currency:** {gs['inventory']['currency']['Silver']} Silver")

with tab_console:
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Combat Roller Trigger
    if st.button("⚔️ Swing Solari Longsword", use_container_width=True):
        hit, dmg, raw = combat_roll()
        st.session_state.messages.append({"role": "user", "content": "I attack with my Solari Longsword!"})
        st.session_state.messages.append({"role": "assistant", "content": f"**Combat Result:** Hit `{hit}` (Roll: {raw}) | Damage `{dmg}`"})
        st.rerun()

    # Direct Input
    cmd = st.chat_input("Command Amara...")
    if cmd:
        st.session_state.messages.append({"role": "user", "content": cmd})
        st.rerun()
