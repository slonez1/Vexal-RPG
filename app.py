import streamlit as st
import re
import json
import base64
import time
from google import genai
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Vexal Engine v3.5", layout="wide", initial_sidebar_state="expanded")

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

# --- 2. GAME DATA ---
MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6}
}

SYSTEM_RULES = r"""
'You are a "Perfectionist" GM narrating an extremely uncensored dark fantasy RPG.'
[... YOUR FULL SYSTEM RULES HERE ...]

### [GM MECHANICAL TAGGING RULES]
You MUST trigger these exactly:
1. NPC Discovery: [NEW NPC: Name | Bio]
2. Travel: [LOCATION: Name | Desc]
3. Combat: [PLAYER DAMAGE: X]
4. Vaxel Activity: [AROUSAL: +X]
5. Quest: [BASTION: +1], [NEW OBJECTIVE: Text]
"""

# --- 3. SESSION STATE ---
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        'name': 'Amara Silvermoon', 'level': 10,
        'hp': 100, 'hp_max': 250, 'mana': 80, 'mana_max': 200, 'stamina': 120, 'stamina_max': 180,
        'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95,
        'location': 'The Spire Entrance', 'vaxel_state': "Active",
        'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
        'skills': {'Martial': {'One-Handed': 10, 'Heavy Armor': 8}, 'Mystical': {'Holy': 10, 'Restoration': 7}},
        'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
        'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
        'equipment': {'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel'}},
        'inventory': {'containers': {'Pouch': {'capacity': 5, 'items': ['Key']}}, 'currency': {'Silver': 150}},
        'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Bastion Shards": 0, "Current Objective": "Enter the Spire."}}
    }

if "messages" not in st.session_state: st.session_state.messages = []
if "audio_id" not in st.session_state: st.session_state.audio_id = 0
if "audio_enabled" not in st.session_state: st.session_state.audio_enabled = True

# --- 4. FUNCTIONS ---
def speak(text, label=""):
    if not st.session_state.audio_enabled: return
    try:
        turn_id = len(st.session_state.messages)
        clean = re.sub(r'\[.*?\]|<.*?>|\*|_|#', '', text).strip()[:4800]
        ssml = f"<speak><prosody volume='soft'>{clean}</prosody></speak>"
        
        response = client_tts.synthesize_speech(
            input=texttospeech.SynthesisInput(ssml=ssml),
            voice=texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-F"),
            audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=0.96, pitch=-1.5)
        )
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        st.markdown(f'<audio class="vexal-audio-current" src="data:audio/mp3;base64,{b64}" id="aud_{turn_id}_{label}"></audio>', unsafe_allow_html=True)
    except: pass

def parse_logic(text):
    gs = st.session_state.game_state
    hp_m = re.search(r'\[PLAYER DAMAGE: (\d+)\]', text)
    ar_m = re.search(r'\[AROUSAL: \+(\d+)\]', text)
    if hp_m: gs['hp'] = max(0, gs['hp'] - int(hp_m.group(1)))
    if ar_m: 
        gs['arousal'] += int(ar_m.group(1))
        if gs['arousal'] >= 100:
            gs['arousal'] = 0
            gs['orgasm_count'] = min(10, gs['orgasm_count'] + 1)

# --- 5. SIDEBAR ---
with st.sidebar:
    gs = st.session_state.game_state
    st.title("🛡️ COMMAND")
    
    # Custom CSS for UI
    st.markdown("""
        <style>
            .stProgress > div > div > div > div { height: 35px !important; border-radius: 5px; }
            div[data-testid="stMetric"] { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
            /* Vitals Colors */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(1) > div > div { background-color: #ff4b4b; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(2) > div > div { background-color: #28a745; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(3) > div > div { background-color: #007bff; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(4) > div > div { background-color: #fd7e14; }
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(5) > div > div { background-color: #e83e8c; }
        </style>
    """, unsafe_allow_html=True)

    st.progress(gs['hp']/gs['hp_max'], text=f"❤️ HP: {gs['hp']}")
    st.progress(gs['stamina']/gs['stamina_max'], text=f"⚡ Stamina: {gs['stamina']}")
    st.progress(gs['mana']/gs['mana_max'], text=f"✨ Mana: {gs['mana']}")
    st.divider()
    st.progress(gs['divine_favor']/100, text=f"⚖️ Divine Favor: {gs['divine_favor']}%")
    
    with st.container(border=True):
        st.markdown("<div style='text-align: center; font-size: 0.8em; opacity: 0.7;'>ATTRIBUTES</div>", unsafe_allow_html=True)
        acols = st.columns(3)
        for i, (k, v) in enumerate(gs['attributes'].items()): acols[i%3].metric(k, v)

    st.subheader("🔗 THE VAXEL")
    st.markdown(f"**State:** `Active`")
    st.progress(gs['arousal']/100, text=f"💓 Arousal: {gs['arousal']}%")
    boxes = "".join(["▣" if i < gs['orgasm_count'] else "▢" for i in range(10)])
    st.markdown(f"**Subjugation Peak:** `{boxes}`")
    
    st.write("---")
    st.session_state.audio_enabled = st.toggle("🔊 Audio Master", value=st.session_state.audio_enabled)

# --- 6. TABS ---
tab_console, tab_char, tab_inv, tab_lore, tab_sett = st.tabs(["📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"])

with tab_console:
    chat_box = st.container(height=500)
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Sequential Audio JavaScript
    st.components.v1.html("""
        <script>
        function playSequential() {
            const audios = window.parent.document.querySelectorAll('.vexal-audio-current');
            let i = 0;
            function playNext() {
                if (i < audios.length) {
                    audios[i].play().catch(e => console.log("Play blocked"));
                    audios[i].onended = () => { i++; playNext(); };
                }
            }
            if (audios.length > 0 && audios[0].paused) { playNext(); }
        }
        setTimeout(playSequential, 500);
        </script>
    """, height=0)

    # --- ACTION BAR (Bottom Justified) ---
    st.write("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    action_text = None

    with c1:
        skills = [s for cat in gs['skills'].values() for s in cat.keys()]
        pick_s = st.selectbox("Skills", skills, label_visibility="collapsed")
        if st.button("💪 Roll Skill", use_container_width=True): action_text = f"I use my {pick_s} skill."
    with c2:
        pick_p = st.selectbox("Spells", gs['known_spells'], label_visibility="collapsed")
        if st.button("✨ Cast", use_container_width=True): action_text = f"I cast {pick_p}."
    with c3:
        if prompt := st.chat_input("Command Amara..."): action_text = prompt

    if action_text:
        st.session_state.messages.append({"role": "user", "content": action_text})
        st.markdown(f'<script>window.parent.document.querySelectorAll(".vexal-audio-current").forEach(el => el.remove());</script>', unsafe_allow_html=True)
        
        with chat_box:
            with st.chat_message("user"): st.markdown(action_text)
            with st.chat_message("assistant"):
                res_box, full_text, last_spoken_idx = st.empty(), "", 0
                st.session_state.audio_id += 1
                stream = client_gemini.models.generate_content_stream(model="gemini-2.0-flash", contents=action_text, config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES))
                
                for chunk in stream:
                    full_text += chunk.text
                    res_box.markdown(full_text + "▌")
                    current_unspoken = full_text[last_spoken_idx:]
                    if len(current_unspoken) > 500 and any(p in current_unspoken for p in [". ", "! ", "\n"]):
                        bp = max(current_unspoken.rfind(p) for p in [". ", "! ", "\n"]) + 1
                        speak(current_unspoken[:bp], label=f"ch_{last_spoken_idx}")
                        last_spoken_idx += bp
                
                res_box.markdown(full_text)
                if len(full_text[last_spoken_idx:].strip()) > 5: speak(full_text[last_spoken_idx:], label="final")
                parse_logic(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
                st.rerun()

# --- 7. REMAINING TABS ---
with tab_char:
    st.header("Proficiencies")
    for cat, sks in gs['skills'].items():
        with st.expander(cat):
            for s, r in sks.items(): st.progress(r/20, text=f"{s}: Rank {r}")

with tab_inv:
    st.subheader("🛡️ Equipped")
    for slot, data in gs['equipment'].items():
        st.write(f"**{slot}:** {data['item']} ({data['material']})")

with tab_lore:
    st.success(f"**Goal:** {gs['lore_ledger']['Main Quest']['Current Objective']}")
    st.write("Known NPCs:", gs['lore_ledger']['NPCs'])

with tab_sett:
    if st.button("💾 Export Save"): st.download_button("Download JSON", json.dumps(gs), "save.json")
    if st.button("⬅️ Undo Last Turn"):
        if len(st.session_state.messages) >= 2:
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
    if st.button("🔥 HARD RESET"):
        st.session_state.clear()
        st.rerun()
