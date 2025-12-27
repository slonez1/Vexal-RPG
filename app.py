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

def parse_logic(text):
    gs = st.session_state.game_state
    
    # --- Vitals Patterns ---
    patterns = {
        'hp': r'\[PLAYER DAMAGE: (\d+)\]',
        'hp_regen': r'\[HP REGEN: \+(\d+)\]',
        'stamina': r'\[STAMINA: ([+-]\d+)\]',
        'mana': r'\[MANA: ([+-]\d+)\]',
        'favor': r'\[DIVINE FAVOR: ([+-]\d+)\]',
        'arousal': r'\[AROUSAL: \+(\d+)\]',
        'mod': r'\[MOD: (\w+) ([+-]\d+)\]'
    }

    # Process Mods (DEX -3, STR +2, etc)
    for mod in re.finditer(patterns['mod'], text):
        attr, val = mod.group(1), int(mod.group(2))
        if attr in gs['attributes']:
            gs['attributes'][attr] += val
            st.toast(f"Stat Changed: {attr} {val}", icon="⚠️")

    # Process Vitals
    hp_d = re.search(patterns['hp'], text)
    hp_r = re.search(patterns['hp_regen'], text)
    if hp_d: gs['hp'] = max(0, gs['hp'] - int(hp_d.group(1)))
    if hp_r: gs['hp'] = min(gs['hp_max'], gs['hp'] + int(hp_r.group(1)))

    sta = re.search(patterns['stamina'], text)
    if sta: gs['stamina'] = max(0, min(gs['stamina_max'], gs['stamina'] + int(sta.group(1))))

    mna = re.search(patterns['mana'], text)
    if mna: gs['mana'] = max(0, min(gs['mana_max'], gs['mana'] + int(mna.group(1))))

    fav = re.search(patterns['favor'], text)
    if fav: gs['divine_favor'] = max(0, 100, gs['divine_favor'] + int(fav.group(1)))

    # Vaxel / Subjugation Logic
    aro = re.search(patterns['arousal'], text)
    if aro:
        gs['arousal'] += int(aro.group(1))
        if gs['arousal'] >= 100:
            gs['arousal'] = 0
            gs['orgasm_count'] += 1
            st.toast("Subjugation Peak Incremented", icon="🔥")
            if gs['orgasm_count'] >= 10:
                gs['vaxel_state'] = "NEURAL OVERLOAD (UNCONSCIOUS)"
                st.error("SYSTEM CRITICAL: Amara has succumbed to Neural Overload.")

    # 1. HP Processing (Damage or Heal)
    dmg = re.search(patterns['hp'], text)
    heal = re.search(patterns['hp_gain'], text)
    if dmg: gs['hp'] = max(0, gs['hp'] - int(dmg.group(1)))
    if heal: gs['hp'] = min(gs['hp_max'], gs['hp'] + int(heal.group(1)))

    # 2. Stamina Processing
    sta = re.search(patterns['stamina'], text)
    if sta: gs['stamina'] = max(0, min(gs['stamina_max'], gs['stamina'] + int(sta.group(1))))

    # 3. Mana Processing
    mna = re.search(patterns['mana'], text)
    if mna: gs['mana'] = max(0, min(gs['mana_max'], gs['mana'] + int(mna.group(1))))

    # 4. Divine Favor Processing
    fav = re.search(patterns['favor'], text)
    if fav: gs['divine_favor'] = max(0, min(100, gs['divine_favor'] + int(fav.group(1))))

    # 5. Arousal & Orgasms
    aro = re.search(patterns['arousal'], text)
    if aro:
        val = int(aro.group(1))
        gs['arousal'] += val
        if gs['arousal'] >= 100:
            gs['arousal'] = 0
            gs['orgasm_count'] = min(10, gs['orgasm_count'] + 1)
            # Add a visual flag for the orgasm event
            st.toast("⚠️ VAXEL OVERLOAD: Subjugation Box Filled!", icon="🔥")

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ COMMAND")
    gs = st.session_state.game_state

    # Custom CSS for Double-Height Progress Bars and Colors
    st.markdown("""
        <style>
            /* The Core Fix: Absolute targeting of progress bars */
            div[data-testid="stSidebar"] .stProgress div[role="progressbar"] > div { height: 30px !important; }
            
            /* Target by color sequence in sidebar */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(1) div[role="progressbar"] > div { background: #ff4b4b !important; } /* HP */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(2) div[role="progressbar"] > div { background: #28a745 !important; } /* Stamina */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(3) div[role="progressbar"] > div { background: #007bff !important; } /* Mana */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(4) div[role="progressbar"] > div { background: #fd7e14 !important; } /* Favor */
            div[data-testid="stSidebar"] [data-testid="stProgress"]:nth-of-type(5) div[role="progressbar"] > div { background: #e83e8c !important; } /* Arousal */
            
            [data-testid="stMetricValue"] { font-size: 1rem !important; }
            [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
        </style>
    """, unsafe_allow_html=True)

    # Vitals
    st.progress(gs['hp']/gs['hp_max'], text=f"❤️ HP: {gs['hp']}/{gs['hp_max']}")
    st.progress(gs['stamina']/gs['stamina_max'], text=f"⚡ Stamina: {gs['stamina']}/{gs['stamina_max']}")
    st.progress(gs['mana']/gs['mana_max'], text=f"✨ Mana: {gs['mana']}/{gs['mana_max']}")
    st.divider()
    st.progress(gs['divine_favor']/100, text=f"⚖️ Divine Favor: {gs['divine_favor']}%")
    
    with st.container(border=True):
        st.markdown("<div style='text-align: center; font-weight: bold; font-size: 0.8em;'>ATTRIBUTES</div>", unsafe_allow_html=True)
        a_cols = st.columns(3)
        for i, (k, v) in enumerate(gs['attributes'].items()):
            a_cols[i%3].metric(k, v)

    st.subheader("🔗 THE VAXEL")
    st.markdown(f"**State:** `{gs['vaxel_state']}`")
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
tab_console, tab_char, tab_inv, tab_lore, tab_sett = st.tabs([
    "📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"
])

with tab_console:
    # --- ACTION BAR (TOP OF CONSOLE) ---
    col1, col2, col3 = st.columns(3)
    pending_action = None
    
    # Chat History Container
    chat_display = st.container(height=500)
    with chat_display:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # JavaScript Coordinator for Sequential Audio
    st.components.v1.html("""
        <script>
        function playSequential() {
            const audios = window.parent.document.querySelectorAll('.vexal-audio-current');
            let i = 0;
            function playNext() {
                if (i < audios.length) {
                    if (audios[i].paused && !audios[i].ended) {
                        audios[i].play().catch(e => console.log("Blocked"));
                        audios[i].onended = () => { i++; playNext(); };
                    } else { i++; playNext(); }
                }
            }
            if (audios.length > 0) playNext();
        }
        setTimeout(playSequential, 1000);
        </script>
    """, height=0)

    # Process Inputs (Chat or Buttons)
    prompt = st.chat_input("Command Amara...")
    actual_prompt = pending_action if pending_action else prompt

    if actual_prompt:
        st.session_state.messages.append({"role": "user", "content": actual_prompt})
        with chat_display:
            with st.chat_message("user"): st.markdown(actual_prompt)
            with st.chat_message("assistant"):
                res_box, full_text, last_spoken_idx = st.empty(), "", 0
                st.session_state.audio_id += 1 

                stream = client_gemini.models.generate_content_stream(
                    model="gemini-2.0-flash", 
                    contents=actual_prompt, 
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_RULES)
                )
                
                for chunk in stream:
                    full_text += chunk.text
                    res_box.markdown(full_text + "▌")
                    
                    unspoken = full_text[last_spoken_idx:]
                    if len(unspoken) > 500 and any(p in unspoken for p in [". ", "! ", "\n"]):
                        break_point = max(unspoken.rfind(p) for p in [". ", "! ", "\n"]) + 1
                        speak(unspoken[:break_point], label=f"ch_{last_spoken_idx}")
                        last_spoken_idx += break_point
                
                res_box.markdown(full_text)
                if len(full_text[last_spoken_idx:].strip()) > 5:
                    speak(full_text[last_spoken_idx:], label="final")
                
                parse_logic(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
                st.rerun()
    # We use session state to "stage" a command from the dropdowns
    if "cmd_buffer" not in st.session_state: st.session_state.cmd_buffer = ""

    col1, col2, col3 = st.columns(3)
    with col1:
        skills = list(SKILL_MAP.keys())
        sel_skill = st.selectbox("Maneuvers", skills, label_visibility="collapsed")
        if st.button("💪 Prep Maneuver", use_container_width=True):
            st.session_state.cmd_buffer = f"I perform a {sel_skill} maneuver "
            
    with col2:
        spells = st.session_state.game_state['known_spells']
        sel_spell = st.selectbox("Spells", spells, label_visibility="collapsed")
        if st.button("✨ Prep Spell", use_container_width=True):
            st.session_state.cmd_buffer = f"I cast {sel_spell} at "

    with col3:
        # This text area is where the buffered text appears for the user to finish
        final_input = st.text_input("Final Command", 
                                    value=st.session_state.cmd_buffer, 
                                    placeholder="Add target or detail...",
                                    label_visibility="collapsed")
        
    if st.button("🚀 EXECUTE ACTION", use_container_width=True):
        if final_input:
            # Process the action through Gemini...
            st.session_state.cmd_buffer = "" # Clear buffer after execution
            # [Insert Gemini streaming and speak logic here]

with tab_char:
    st.header("Proficiencies")
    for cat, skills in gs['skills'].items():
        with st.expander(cat):
            for s, r in skills.items(): st.progress(r/20, text=f"{s}: Rank {r}")
    st.subheader("Spellbook")
    for s in gs['known_spells']: st.info(f"✨ {s} (Cost: {gs['mana_costs'].get(s, 0)} MP)")
    st.divider()
    st.subheader("📊 Recent Vital Changes")
    # This creates a small scrolling log of the last few messages' impact
    for msg in st.session_state.messages[-3:]:
        if "[" in msg['content'] and "]" in msg['content']:
            tags = re.findall(r'\[.*?\]', msg['content'])
            if tags:
                st.caption(f"Last Turn Impacts: {', '.join(tags)}")

with tab_inv:
    st.subheader("🛡️ Equipped")
    for slot, data in gs['equipment'].items():
        p = MAT_PROPS.get(data['material'], {"DT":0, "Weight":0, "Noise":0})
        st.write(f"**{slot}:** {data['item']} ({data['material']}) | Prot: +{p['DT']} | Noise: {p['Noise']}")
    st.subheader("🧺 Containers")
    for c, data in gs['inventory']['containers'].items():
        with st.expander(f"{c} ({len(data['items'])}/{data['capacity']})"):
            for i in data['items']: st.write(f"- {i}")
    st.write(f"**Currency:** {gs['inventory']['currency']['Silver']} Silver")

with tab_lore:
    l = gs['lore_ledger']
    st.success(f"**Quest:** {l['Main Quest']['Current Objective']} ({l['Main Quest']['Bastion Shards']}/7 Shards)")
    st.write("### Known Locations", l['Locations'])
    st.write("### Persons of Interest", l['NPCs'])

with tab_sett:
    with st.expander("💾 Memory Management"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.download_button("📥 Export Save (.json)", json.dumps(gs), file_name="vexal_chronicle.json", use_container_width=True)
        with col_s2:
            uploaded = st.file_uploader("📂 Import Save", type="json")
            if uploaded:
                st.session_state.game_state = json.load(uploaded)
                st.rerun()

    if st.button("🔥 WIPE SYSTEM (Hard Reset)", type="primary"):
        st.session_state.clear()
        st.rerun()
