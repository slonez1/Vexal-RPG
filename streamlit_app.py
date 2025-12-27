import streamlit as st
import re
import base64
from google import genai
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. BOILERPLATE ---
st.set_page_config(page_title="Vexal RPG", layout="wide")
st.write("### 🚀 VEXAL ENGINE V3.0") # Visual check for update

# Authentication
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)
client_gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Session State
if "messages" not in st.session_state: st.session_state.messages = []
if "audio_id" not in st.session_state: st.session_state.audio_id = 0

# --- 2. TOP DASHBOARD ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    v_choice = st.selectbox("Narrator:", ["Zephyr", "Kore", "Charon"])
    v_map = {"Zephyr": "en-US-Chirp3-HD-Zephyr", "Kore": "en-US-Chirp3-HD-Kore", "Charon": "en-US-Chirp3-HD-Charon"}
with col2:
    st.write("##")
    if st.button("🚫 STOP AUDIO", type="primary", use_container_width=True):
        st.session_state.audio_id += 1
        st.rerun()
with col3:
    st.write("##")
    if st.button("🗑️ RESET STORY", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio_id += 1
        st.rerun()

# --- 3. AUDIO FUNCTION ---
def speak(text, label=""):
    try:
        clean = re.sub(r'\*|_|#|>', '', text).strip()[:4800]
        input_tts = texttospeech.SynthesisInput(text=clean)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=v_map[v_choice])
        config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client_tts.synthesize_speech(input=input_tts, voice=voice, audio_config=config)
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        
        # Audio player with unique ID to prevent double-narration
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}" id="aud_{st.session_state.audio_id}_{label}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 4. MAIN INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command the Vexal..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_box = st.empty()
        full_text = ""
        audio_triggered = False
        st.session_state.audio_id += 1

        # Using the NEW Google GenAI streaming method
        stream = client_gemini.models.generate_content_stream(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        
        for chunk in stream:
            full_text += chunk.text
            res_box.markdown(full_text + "▌")
            
            # TRIGGER AUDIO FAST (after ~400 chars)
            if not audio_triggered and len(full_text) > 400:
                audio_triggered = True
                with st.status("Voice manifesting..."):
                    speak(full_text, "Part1")
        
        res_box.markdown(full_text)
        
        # Handle the Part II for long stories
        if len(full_text) > 4800:
            mid = full_text.rfind('.', 0, 4800) + 1
            speak(full_text[mid:], "Part2")
        elif not audio_triggered:
            speak(full_text, "Full")

    st.session_state.messages.append({"role": "assistant", "content": full_text})
