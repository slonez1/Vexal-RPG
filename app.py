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
st.set_page_config(page_title="Vexal Engine", layout="wide", initial_sidebar_state="expanded")

# Authentication & Clients
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
[... INCLUDE YOUR FULL 7-PARAGRAPH SYSTEM RULES HERE ...]

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

# --- 3. SESSION STATE (The Cabinet) ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'name': 'Amara Silvermoon', 'level': 10,
        'hp': 100, 'hp_max': 250,
        'mana': 30, 'mana_max': 200,
        'stamina': 100, 'stamina_max': 180,
        'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95,
        'location': 'The Spire Entrance',
        'vaxel_state': "Active",
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

# --- 4. ENGINE FUNCTIONS ---
def speak(text, label=""):
    try:
        clean = re.sub(r'\[.*?\]|<.*?>|\*|_|#', '', text).strip()[:4800]
        v_map = {"Zephyr": "en-US-Chirp3-HD-Zephyr", "Kore": "en-US-Chirp3-HD-Kore", "Charon": "en-US-Chirp3-HD-Charon"}
        v_choice = st.session_state.get("narrator", "Zephyr")
        input_tts = texttospeech.TextToSpeechClient().synthesize_speech(
            input=texttospeech.SynthesisInput(text=clean),
            voice=texttospeech.VoiceSelectionParams(language_code="en-US", name=v_map[v_choice]),
            audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        )
        b64 = base64.b64encode(input_tts.audio_content).decode("utf-8")
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}" id="aud_{st.session_state.audio_id}_{label}">', unsafe_allow_html=True)
    except: pass

def parse_logic(text):
    gs = st.session_state.game_state
    # Combat/Vaxel
    hp_m = re.search(r'\[PLAYER DAMAGE: (.*?)\]', text)
    ar_m = re.search(r'\[AROUSAL: \+(.*?)\]', text)
    if hp_m: gs['hp'] = max(0, gs['hp'] - int(hp_m.group(1)))
    if ar_m: gs['arousal'] += int(ar_m.group(1))
    if gs['arousal'] >= 100:
        gs['arousal'] = 0
        gs['orgasm_count'] += 1
    # Lore/Quest
    npc_m = re.search(r'\[NEW NPC: (.*?) \| (.*?)\]', text)
    loc_m = re.search(r'\[LOCATION: (.*?) \| (.*?)\]', text)
    obj_m = re.search(r'\[NEW OBJECTIVE: (.*?)\]', text)
    shrd_m = re.search(r'\[BASTION: \+1\]', text)
    if npc_m: gs['lore_ledger']['NPCs'][npc_m.group(1).strip()] = npc_m.group(2).strip()
    if loc_m: 
        gs['lore_ledger']['Locations'][loc_m.group(1).strip()] = loc_m.group(2).strip()
        gs['location'] = loc_m.group(1).strip()
    if obj_m: gs['lore_ledger']['Main Quest']['Current Objective'] = obj_m.group(1).strip()
    if shrd_m: gs['lore_ledger']['Main Quest']['Bastion Shards'] += 1

# --- 5. UI LAYOUT ---
st.markdown("<h1 style='text-align: center; color: #8e44ad;'>VEXAL ENGINE v3.5</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛡️ COMMAND")
    st.session_state.narrator = st.selectbox("Narrator:", ["Zephyr", "Kore", "Charon"])
    gs = st.session_state.game_state
    st.progress(gs['hp']/gs['hp_max'], text=f"HP: {gs['hp']}/{gs['hp_max']}")
    st.progress(gs['arousal']/100, text=f"Arousal: {gs['arousal']}%")
    st.write(f"**Location:** {gs['location']}")
    cols = st.columns(3)
    for i, (k, v) in enumerate(gs['attributes'].items()): cols[i%3].metric(k, v)

tab_console, tab_char, tab_inv, tab_lore, tab_sett = st.tabs(["📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"])

with tab_console:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("Command Amara..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            res_box, full_text, audio_triggered = st.empty(), "", False
            st.session_state.audio_id += 1
            stream = client_gemini.models.generate_content_stream(model="gemini-2.0-flash", contents=prompt, config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES))
            for chunk in stream:
                full_text += chunk.text
                res_box.markdown(full_text + "▌")
                if not audio_triggered and len(full_text) > 400:
                    audio_triggered = True
                    speak(full_text, "Start")
            res_box.markdown(full_text)
            if not audio_triggered: speak(full_text, "Full")
            parse_logic(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

with tab_char:
    st.header("Proficiencies")
    for cat, skills in gs['skills'].items():
        with st.expander(cat):
            for s, r in skills.items(): st.progress(r/20, text=f"{s}: Rank {r}")
    st.subheader("Spellbook")
    for s in gs['known_spells']: st.info(f"✨ {s} (Cost: {gs['mana_costs'].get(s, 0)} MP)")

with tab_inv:
    st.subheader("🛡️ Equipped")
    for slot, data in gs['equipment'].items():
        p = MAT_PROPS.get(data['material'], {"DT":0, "Weight":0, "Noise":0})
        st.write(f"**{slot}:** {data['item']} ({data['material']}) | Prot: +{p['DT']} | Noise: {p['Noise']}")
    st.subheader("🧺 Containers")
    for c, data in gs['inventory']['containers'].items():
        with st.expander(f"{c} ({len(data['items'])}/{data['capacity']})"):
            for i in data['items']: st.write(f"- {i}")

with tab_lore:
    l = gs['lore_ledger']
    st.success(f"**Quest:** {l['Main Quest']['Current Objective']} ({l['Main Quest']['Bastion Shards']}/7 Shards)")
    st.write("### Known Locations", l['Locations'])
    st.write("### Persons of Interest", l['NPCs'])

with tab_sett:
    if st.button("💾 Download Save"):
        st.download_button("Save JSON", json.dumps(gs), "save.json")
    if st.button("🔥 RESET GAME", type="primary"):
        st.session_state.clear()
        st.rerun()
