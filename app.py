import streamlit as st
import re
import json
import base64
from google import genai
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. CONFIGURATION & AUTH ---
st.set_page_config(page_title="The Spire: Vaxel Engine", layout="wide", initial_sidebar_state="expanded")

# Initialize Clients
@st.cache_resource
def init_clients():
    gcp_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(gcp_info)
    client_tts = texttospeech.TextToSpeechClient(credentials=creds)
    client_gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    return client_tts, client_gemini

client_tts, client_gemini = init_clients()

# --- 2. THE BRAIN (System Instructions) ---
SYSTEM_RULES = r"""
[... Paste your full SYSTEM_RULES text here exactly as provided in Cell 1 ...]
"""

# --- 3. THE CABINET (State Management) ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'name': 'Amara Silvermoon', 'level': 10,
        'hp': 100, 'hp_max': 250,
        'mana': 30, 'mana_max': 200,
        'stamina': 100, 'stamina_max': 180,
        'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95,
        'vaxel_state': "Active",
        'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
        'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal', 'Mana Shield'],
        'equipment': {'Torso': 'Knight-Commander Plate', 'MainHand': 'Solari Longsword'},
        'inventory': {'Silver': 150, 'items': ['Whetstone', 'Holy Oil']},
        'lore_ledger': {'Main Quest': "Enter the Spire."}
    }

if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_id" not in st.session_state:
    st.session_state.audio_id = 0

# --- 4. THE VOICE ENGINE ---
def speak(text, label=""):
    try:
        clean = re.sub(r'\[.*?\]|<.*?>|\*|_|#', '', text).strip()[:4800]
        v_map = {"Zephyr": "en-US-Chirp3-HD-Zephyr", "Kore": "en-US-Chirp3-HD-Kore", "Charon": "en-US-Chirp3-HD-Charon"}
        v_choice = st.session_state.get("narrator", "Zephyr")
        
        input_tts = texttospeech.SynthesisInput(text=clean)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=v_map[v_choice])
        config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client_tts.synthesize_speech(input=input_tts, voice=voice, audio_config=config)
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}" id="aud_{st.session_state.audio_id}_{label}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 5. PARSE LOGIC (The "Bridge") ---
def parse_logic(text):
    """Extracts stats from [TAGS] in AI response."""
    hp_change = re.search(r'\[PLAYER DAMAGE: (.*?)\]', text)
    arousal_change = re.search(r'\[AROUSAL: \+(.*?)\]', text)
    
    if hp_change:
        st.session_state.game_state['hp'] -= int(hp_change.group(1))
    if arousal_change:
        st.session_state.game_state['arousal'] += int(arousal_change.group(1))
    
    if st.session_state.game_state['arousal'] >= 100:
        st.session_state.game_state['arousal'] = 0
        st.session_state.game_state['orgasm_count'] += 1

# --- 6. PRISM UI (Sidebar & Tabs) ---
with st.sidebar:
    st.title("🛡️ VAXEL COMMAND")
    st.session_state.narrator = st.selectbox("Narrator:", ["Zephyr", "Kore", "Charon"])
    
    # Vitals
    gs = st.session_state.game_state
    st.progress(gs['hp']/gs['hp_max'], text=f"HP: {gs['hp']}/{gs['hp_max']}")
    st.progress(gs['arousal']/100, text=f"Arousal: {gs['arousal']}%")
    st.write(f"**Peaks:** {'●' * gs['orgasm_count']}{'○' * (10-gs['orgasm_count'])}")
    
    # Attributes Grid
    cols = st.columns(3)
    for i, (k, v) in enumerate(gs['attributes'].items()):
        cols[i%3].metric(k, v)

    if st.button("🗑️ RESET STORY", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Interface
tab_console, tab_char, tab_inv = st.tabs(["📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY"])

with tab_console:
    # Display Chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input handling
    if prompt := st.chat_input("Command Amara..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            res_box = st.empty()
            full_text = ""
            audio_triggered = False
            st.session_state.audio_id += 1

            stream = client_gemini.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES)
            )
            
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
    st.json(st.session_state.game_state['attributes'])
    st.write("### Known Spells")
    st.write(st.session_state.game_state['known_spells'])

with tab_inv:
    st.write("### Equipment")
    st.table(st.session_state.game_state['equipment'])
