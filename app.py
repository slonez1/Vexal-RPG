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
# --- 4. REFINED VEXAL VOICE ENGINE (Zephyr Only) ---
def speak(text, label=""):
    if not st.session_state.get("audio_enabled", True):
        return
        
    try:
        # TWEAK THESE THREE VALUES BASED ON YOUR DEMO FINDINGS:
        target_voice = "en-US-Neural2-F" # High-end intimate voice
        target_speed = 0.96              # Closer to 1.0 is more natural
        target_pitch = -1.5              # Lower is more resonant
        
        clean = re.sub(r'\[.*?\]|<.*?>|\*|_|#', '', text).strip()[:4800]
        
        # Wrapping in SSML to force a "soft" delivery
        ssml_text = f"<speak><prosody volume='soft'>{clean}</prosody></speak>"
        
        input_tts = texttospeech.SynthesisInput(ssml=ssml_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            name=target_voice
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=target_speed,
            pitch=target_pitch
        )
        
        response = client_tts.synthesize_speech(
            input=input_tts, 
            voice=voice, 
            audio_config=audio_config
        )
        
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}" id="aud_{st.session_state.audio_id}_{label}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

def parse_logic(text):
    gs = st.session_state.game_state
    # Combat/Vaxel
    hp_m = re.search(r'\[PLAYER DAMAGE: (.*?)\]', text)
    ar_m = re.search(r'\[AROUSAL: \+(.*?)\]', text)
    if hp_m: gs['hp'] = max(0, gs['hp'] - int(hp_m.group(1)))
    if ar_m: gs['arousal'] += int(ar_m.group(1))if prompt := st.chat_input("Command Amara..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            res_box = st.empty()
            full_text = ""
            last_spoken_idx = 0  # Tracks where the voice is at
            st.session_state.audio_id += 1 

            stream = client_gemini.models.generate_content_stream(
                model="gemini-2.0-flash", 
                contents=prompt, 
                config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES)
            )
            
            for chunk in stream:
                full_text += chunk.text
                res_box.markdown(full_text + "▌")
                
                # AUDIO CHUNKING LOGIC:
                # If we have at least 500 new characters AND the AI just finished a sentence...
                current_unspoken = full_text[last_spoken_idx:]
                if len(current_unspoken) > 500 and any(p in current_unspoken for p in [". ", "! ", "? ", "\n"]):
                    # Find the last sentence end to keep the narration natural
                    break_point = max(current_unspoken.rfind(p) for p in [". ", "! ", "? ", "\n"]) + 1
                    chunk_to_speak = current_unspoken[:break_point]
                    
                    speak(chunk_to_speak, label=f"chunk_{last_spoken_idx}")
                    last_spoken_idx += break_point
            
            # Finalize: Speak any remaining text that didn't hit the 500 char limit
            res_box.markdown(full_text)
            remaining_text = full_text[last_spoken_idx:]
            if len(remaining_text.strip()) > 5:
                speak(remaining_text, label="final")
                
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
    st.header("⚙️ Vexal System Settings")
    
    # --- AUDIO BLOCK ---
    with st.expander("🔊 Audio & Narrator Settings", expanded=True):
        st.session_state.audio_enabled = st.toggle("Voice Narration Active", value=True)
        st.session_state.narrator = st.radio(
            "Narrator Persona", 
            ["Zephyr", "Kore", "Charon"], 
            horizontal=True,
            help="Zephyr: Intimate/Breathy | Kore: Clear/Direct | Charon: Deep/Ancient"
        )
        if st.button("🔄 Restart Audio Engine"):
            st.session_state.audio_id += 1
            st.rerun()

    # --- SAVE/LOAD BLOCK ---
    with st.expander("💾 Memory Management"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.download_button(
                "📥 Export Save (.json)",
                json.dumps(st.session_state.game_state),
                file_name="vexal_chronicle.json",
                use_container_width=True
            )
        with col_s2:
            uploaded = st.file_uploader("📂 Import Save", type="json")
            if uploaded:
                st.session_state.game_state = json.load(uploaded)
                st.success("State Uploaded! Click 'Reboot' to apply.")

    # --- RESET ---
    st.divider()
    if st.button("🔥 WIPE SYSTEM (Hard Reset)", type="primary"):
        st.session_state.clear()
        st.rerun()
