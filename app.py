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

# --- 3. SESSION STATE ---
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
    if not st.session_state.get("audio_enabled", True): return
    try:
        # We add a unique turn_id so JS knows which clips belong to the latest response
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
        
        # We use 'vexal-audio-current' to distinguish from previous turns
        st.markdown(f'<audio class="vexal-audio-current" src="data:audio/mp3;base64,{b64}" id="aud_{turn_id}_{label}"></audio>', unsafe_allow_html=True)
    except Exception as e: pass

def parse_logic(text):
    gs = st.session_state.game_state
    # --- HP/Damage Safety Check ---
    hp_m = re.search(r'\[PLAYER DAMAGE: (\d+)\]', text) # \d+ ensures it only looks for numbers
    ar_m = re.search(r'\[AROUSAL: \+(\d+)\]', text)
    
    if hp_m:
        try:
            val = int(hp_m.group(1))
            gs['hp'] = max(0, gs['hp'] - val)
        except ValueError: pass # Ignores [PLAYER DAMAGE: X]
    
    if ar_m:
        try:
            val = int(ar_m.group(1))
            gs['arousal'] += val
            if gs['arousal'] >= 100:
                gs['arousal'] = 0
                gs['orgasm_count'] = min(10, gs['orgasm_count'] + 1)
        except ValueError: pass

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ COMMAND")
    gs = st.session_state.game_state

    # Custom CSS for Double-Height Progress Bars and Colors
    st.markdown("""
        <style>
            .stProgress > div > div > div > div { height: 30px !important; }
            /* Specific Colors */
            div[data-testid="stv-hp"] .stProgress > div > div { background-color: #ff4b4b; }
            div[data-testid="stv-stamina"] .stProgress > div > div { background-color: #28a745; }
            div[data-testid="stv-mana"] .stProgress > div > div { background-color: #007bff; }
            div[data-testid="stv-favor"] .stProgress > div > div { background-color: #fd7e14; }
            div[data-testid="stv-arousal"] .stProgress > div > div { background-color: #e83e8c; }
        </style>
    """, unsafe_allow_html=True)

    # Vitals
    st.container(border=True).markdown("### Vitals")
    st.progress(gs['hp']/gs['hp_max'], text=f"❤️ HP: {gs['hp']}")
    st.progress(gs['stamina']/gs['stamina_max'], text=f"⚡ Stamina: {gs['stamina']}")
    st.progress(gs['mana']/gs['mana_max'], text=f"✨ Mana: {gs['mana']}")
    st.divider()
    st.progress(gs['divine_favor']/100, text=f"⚖️ Divine Favor: {gs['divine_favor']}%")
    
    # Attributes in a Fancy Container
    with st.container(border=True):
        st.markdown("<div style='text-align: center; font-weight: bold;'>ATTRIBUTES</div>", unsafe_allow_html=True)
        a_cols = st.columns(3)
        for i, (k, v) in enumerate(gs['attributes'].items()):
            a_cols[i%3].metric(k, v)

    # The Vaxel Section
    st.subheader("🔗 THE VAXEL")
    st.progress(gs['arousal']/100, text=f"💓 Arousal: {gs['arousal']}%")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")
    
    # Bottom Sidebar Audio Control
    st.write("---")
    st.session_state.audio_enabled = st.toggle("🔊 Audio Master", value=st.session_state.get("audio_enabled", True))

# --- 6. THE UI TABS ---
tab_console, tab_char, tab_inv, tab_lore, tab_sett = st.tabs([
    "📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"
])



    # JavaScript Coordinator for Audio
    st.components.v1.html("""
        <script>
        function playNext(index) {
            const audios = window.parent.document.querySelectorAll('.vexal-audio');
            if (index < audios.length) {
                // Remove any 'played' flags from previous refreshes
                if (audios[index].paused && !audios[index].ended) {
                    audios[index].play().catch(e => console.log("Autoplay blocked"));
                    audios[index].onended = () => playNext(index + 1);
                } else {
                    playNext(index + 1);
                }
            }
        }
        setInterval(() => playNext(0), 2000);
        </script>
    """, height=0)

with tab_char:
    st.header("Proficiencies")
    gs = st.session_state.game_state # Ensure gs is local to the tab
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
    # AUDIO TOGGLE
    st.session_state.audio_enabled = st.toggle("Audio Narration", value=st.session_state.get("audio_enabled", True))
    
    # UNDO BUTTON
    if st.button("⬅️ Undo Last Turn"):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.success("Last turn erased from memory.")
            st.rerun()

    with st.expander("💾 Memory Management"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.download_button("📥 Export Save (.json)", json.dumps(st.session_state.game_state), file_name="vexal_chronicle.json", use_container_width=True)
        with col_s2:
            uploaded = st.file_uploader("📂 Import Save", type="json")
            if uploaded:
                st.session_state.game_state = json.load(uploaded)
                st.success("State Uploaded! Click 'Reboot' to apply.")

    st.divider()
    if st.button("🔥 WIPE SYSTEM (Hard Reset)", type="primary"):
        st.session_state.clear()
        st.rerun()

with tab_console:
    # --- ACTION BAR ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        all_skills = [s for cat in gs['skills'].values() for s in cat.keys()]
        selected_skill = st.selectbox("Use Skill", all_skills, label_visibility="collapsed")
        if st.button("💪 Roll Skill", use_container_width=True):
            st.session_state.pending_action = f"I use my {selected_skill} skill."
            
    with col2:
        selected_spell = st.selectbox("Cast Spell", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Cast Spell", use_container_width=True):
            st.session_state.pending_action = f"I cast {selected_spell}."
            
    with col3:
        impromp = st.text_input("Impromptu...", label_visibility="collapsed", placeholder="Scream, hide, etc...")
        if st.button("💥 Execute", use_container_width=True):
            st.session_state.pending_action = impromp

 if prompt := st.chat_input("Command Amara..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
            
        with st.chat_message("assistant"):
            res_box, full_text, last_spoken_idx = st.empty(), "", 0
            st.session_state.audio_id += 1 

            stream = client_gemini.models.generate_content_stream(
                model="gemini-2.0-flash", 
                contents=prompt, 
                config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES)
            )
            
            for chunk in stream:
                full_text += chunk.text
                res_box.markdown(full_text + "▌")
                
                current_unspoken = full_text[last_spoken_idx:]
                if len(current_unspoken) > 500 and any(p in current_unspoken for p in [". ", "! ", "? ", "\n"]):
                    break_point = max(current_unspoken.rfind(p) for p in [". ", "! ", "? ", "\n"]) + 1
                    speak(current_unspoken[:break_point], label=f"chunk_{last_spoken_idx}")
                    last_spoken_idx += break_point
            
            res_box.markdown(full_text)
            if len(full_text[last_spoken_idx:].strip()) > 5:
                speak(full_text[last_spoken_idx:], label="final")
            
            parse_logic(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
