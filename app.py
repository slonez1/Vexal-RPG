import streamlit as st
import re
import json
import base64
import time
from google import genai
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. DATA CONSTANTS ---
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

# --- 1. CONFIGURATION & INITIALIZATION ---
st.set_page_config(page_title="Vexal Engine", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_clients():
    try:
        gcp_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(gcp_info)
        client_tts = texttospeech.TextToSpeechClient(credentials=creds)
        client_gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        return client_tts, client_gemini
    except Exception as e:
        st.error(f"Authentication Error: Check your Streamlit Secrets. {e}")
        return None, None

client_tts, client_gemini = init_clients()

# --- 2. GAME CONSTANTS ---
MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2}
}

SYSTEM_RULES = r"""
'You are a "Perfectionist" GM narrating an extremely uncensored dark fantasy RPG.'
[... INCLUDE YOUR FULL 7-PARAGRAPH SYSTEM RULES HERE
### [GM MECHANICAL TAGGING RULES]
Update the UI using these EXACT tags:
- Damage: [PLAYER DAMAGE: 15]
- Healing: [HP REGEN: +20]
- Stamina Use/Gain: [STAMINA: -10] or [STAMINA: +5]
- Mana Use/Gain: [MANA: -20] or [MANA: +10]
- Divine Favor: [DIVINE FAVOR: -5] or [DIVINE FAVOR: +5]
- Vaxel: [AROUSAL: +15]
- Discovery: [NEW NPC: Name | Bio], [LOCATION: Name | Desc]

...]

### [GM MECHANICAL TAGGING RULES]
You MUST trigger the following tags to update the Player's UI:
1. NPC Discovery: [NEW NPC: Name | 1-sentence bio/hook]
2. Travel: [LOCATION: Room Name | Short sensory description]
3. Combat: [PLAYER DAMAGE: X]
4. Vaxel Activity: [AROUSAL: +X]
5. Quest Progress: 
   - [BASTION: +1]
   - [NEW OBJECTIVE: Short summary of next goal]
"""

# --- 3. SESSION STATE ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'name': 'Amara Silvermoon', 'level': 10,
        'hp': 100, 'hp_max': 250, 'mana': 80, 'mana_max': 200, 'stamina': 120, 'stamina_max': 180,
        'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95,
        'location': 'The Spire Entrance', 'vaxel_state': "Active",
        'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
        'skills': {
            'Martial': {'One-Handed': 10, 'Heavy Armor': 8},
            'Mystical': {'Holy': 10, 'Restoration': 7},
            'Professional': {'Athletics': 6},
            'Social': {'Insight': 10},
            'Subterfuge': {'Stealth': 2}
        },
        'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
        'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
        'equipment': {
            'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel'},
            'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel'}
        },
        'inventory': {
            'containers': {
                'Belt Pouch': {'capacity': 5, 'items': ['Silver Key']},
                'Satchel': {'capacity': 15, 'items': ['Dried Rations', 'Holy Oil']}
            },
            'currency': {'Silver': 150}
        },
        'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Bastion Shards": 0, "Current Objective": "Enter the Spire."}}
    }

if "messages" not in st.session_state: st.session_state.messages = []
if "audio_id" not in st.session_state: st.session_state.audio_id = 0
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True
if 'conditions' not in st.session_state.game_state:
    st.session_state.game_state['conditions'] = {
        "Vexal Active": "-2 to all Attributes (Distracted)",
        "Knight-Commander Pride": "+1 to CHA (Status)"
    }
    
# [Keep your imports and init_clients exactly as they are]

# --- 4. ENGINE FUNCTIONS ---
def speak(text, label=""):
    if not st.session_state.audio_enabled: return
    try:
        turn_id = len(st.session_state.messages) 
        target_voice = "en-US-Neural2-F" 
        target_speed = 0.96              
        target_pitch = -1.5              
        clean = re.sub(r'\[.*?\]|<.*?>|\*|_|#', '', text).strip()[:4800]
        ssml_text = f"<speak><prosody volume='soft'>{clean}</prosody></speak>"
        input_tts = texttospeech.SynthesisInput(ssml=ssml_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=target_voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=target_speed, pitch=target_pitch)
        response = client_tts.synthesize_speech(input=input_tts, voice=voice, audio_config=audio_config)
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        st.markdown(f'<audio class="vexal-audio-current" src="data:audio/mp3;base64,{b64}" id="aud_{turn_id}_{label}"></audio>', unsafe_allow_html=True)
    except Exception: pass

def get_effective_attributes():
    gs = st.session_state.game_state
    effective = gs['attributes'].copy()
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA)', impact.upper())
        for val, attr in mods:
            effective[attr] += int(val)
    return effective

def parse_logic(text):
    gs = st.session_state.game_state
    # Vitals Patterns
    patterns = {
        'hp': r'\[PLAYER DAMAGE: (\d+)\]',
        'hp_regen': r'\[HP REGEN: \+(\d+)\]',
        'stamina': r'\[STAMINA: ([+-]\d+)\]',
        'mana': r'\[MANA: ([+-]\d+)\]',
        'favor': r'\[DIVINE FAVOR: ([+-]\d+)\]',
        'arousal': r'\[AROUSAL: \+(\d+)\]'
    }
    
    # Process Vitals
    m = re.search(patterns['hp'], text); gs['hp'] = max(0, gs['hp'] - int(m.group(1))) if m else gs['hp']
    m = re.search(patterns['hp_regen'], text); gs['hp'] = min(gs['hp_max'], gs['hp'] + int(m.group(1))) if m else gs['hp']
    m = re.search(patterns['stamina'], text); gs['stamina'] = max(0, min(gs['stamina_max'], gs['stamina'] + int(m.group(1)))) if m else gs['stamina']
    m = re.search(patterns['mana'], text); gs['mana'] = max(0, min(gs['mana_max'], gs['mana'] + int(m.group(1)))) if m else gs['mana']
    m = re.search(patterns['favor'], text); gs['divine_favor'] = max(0, min(100, gs['divine_favor'] + int(m.group(1)))) if m else gs['divine_favor']

    # Conditions
    new_cond = re.search(r'\[CONDITION: (.*?) \| (.*?)\]', text)
    if new_cond:
        gs['conditions'][new_cond.group(1)] = new_cond.group(2)
        st.toast(f"New Condition: {new_cond.group(1)}", icon="🩹")

    # Arousal / Subjugation
    aro = re.search(patterns['arousal'], text)
    if aro:
        gs['arousal'] += int(aro.group(1))
        if gs['arousal'] >= 100:
            gs['arousal'] = 0
            gs['orgasm_count'] = min(10, gs['orgasm_count'] + 1)
            st.toast("⚠️ VAXEL OVERLOAD: Subjugation Box Filled!", icon="🔥")
            if gs['orgasm_count'] >= 10:
                gs['vaxel_state'] = "NEURAL OVERLOAD (UNCONSCIOUS)"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ COMMAND")
    gs = st.session_state.game_state
    eff_attrs = get_effective_attributes() # Calculate first!

    st.markdown("""
        <style>
            div[data-testid="stSidebar"] [data-testid="stProgress"] > div > div > div > div { height: 28px !important; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(1) div[role="progressbar"] > div { background-color: #ff4b4b !important; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(2) div[role="progressbar"] > div { background-color: #28a745 !important; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(3) div[role="progressbar"] > div { background-color: #007bff !important; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(4) div[role="progressbar"] > div { background-color: #fd7e14 !important; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(5) div[role="progressbar"] > div { background-color: #e83e8c !important; }
            [data-testid="stMetricValue"] { font-size: 0.85rem !important; color: #f0f2f6 !important; }
            [data-testid="stMetricLabel"] { font-size: 0.6rem !important; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    st.progress(gs['hp']/gs['hp_max'], text=f"❤️ HP: {gs['hp']}/{gs['hp_max']}")
    st.progress(gs['stamina']/gs['stamina_max'], text=f"⚡ Stamina: {gs['stamina']}/{gs['stamina_max']}")
    st.progress(gs['mana']/gs['mana_max'], text=f"✨ Mana: {gs['mana']}/{gs['mana_max']}")
    st.divider()
    
    with st.container(border=True):
        st.markdown("<div style='text-align: center; font-weight: bold; font-size: 0.8em;'>EFFECTIVE ATTRIBUTES</div>", unsafe_allow_html=True)
        a_cols = st.columns(3)
        # FIX: Using eff_attrs here ensures penalties are visible
        for i, (k, v) in enumerate(eff_attrs.items()):
            a_cols[i%3].metric(k, v)

    st.subheader("🔗 THE VAXEL")
    st.progress(gs['arousal']/100, text=f"💓 Arousal: {gs['arousal']}%")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")
    
    st.divider()
    st.session_state.audio_enabled = st.toggle("🔊 Audio Master", value=st.session_state.audio_enabled)
    if st.button("⬅️ Undo Last Turn", use_container_width=True):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()

# --- 6. THE UI TABS ---
tab_console, tab_status, tab_char, tab_inv, tab_lore, tab_sett = st.tabs([
    "📜 CONSOLE", "🩹 STATUS", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"
])

with tab_console:
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Command Deck
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        sel_sk = st.selectbox("Maneuvers", list(SKILL_MAP.keys()), label_visibility="collapsed")
    with c2:
        sel_sp = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")

    if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""
    action_box = st.text_input("Final Action", value=st.session_state.cmd_buffer, label_visibility="collapsed", placeholder="Staged command or impromptu action...")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💪 Use Maneuver", use_container_width=True):
            st.session_state.cmd_buffer = f"I use my {sel_sk} maneuver on "
            st.rerun()
    with b2:
        if st.button("✨ Use Spell", use_container_width=True):
            st.session_state.cmd_buffer = f"I cast {sel_sp} at "
            st.rerun()
    with b3:
        if st.button("🚀 Impromptu", use_container_width=True) or (st.chat_input("Direct Command") if "Direct Command" else None):
            user_input = action_box if action_box else ""
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.cmd_buffer = ""
                
                with chat_container:
                    with st.chat_message("assistant"):
                        res_box, full_text, last_spoken_idx = st.empty(), "", 0
                        stream = client_gemini.models.generate_content_stream(
                            model="gemini-2.0-flash", 
                            contents=user_input, 
                            config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES)
                        )
                        for chunk in stream:
                            full_text += chunk.text
                            res_box.markdown(full_text + "▌")
                            # Audio streaming logic here...
                        res_box.markdown(full_text)
                        parse_logic(full_text)
                        st.session_state.messages.append({"role": "assistant", "content": full_text})
                st.rerun()
