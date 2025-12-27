import streamlit as st
import google.generativeai as genai
from google.cloud import texttospeech
from google.oauth2 import service_account
import base64
import re

# --- 1. BOILERPLATE & AUTH ---
st.set_page_config(page_title="Vexal RPG", layout="wide")

# Persistent State
if "messages" not in st.session_state: st.session_state.messages = []
if "audio_playing" not in st.session_state: st.session_state.audio_playing = False
if "audio_id" not in st.session_state: st.session_state.audio_id = 0

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-latest')

gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)

# --- 2. CONTROL DASHBOARD (Top of Page) ---
st.title("🌌 The Vexal Chronicles")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    v_choice = st.selectbox("Narrator:", ["Zephyr (Bright)", "Kore (Steady)", "Charon (Deep)"])
    v_map = {"Zephyr (Bright)": "en-US-Chirp3-HD-Zephyr", "Kore (Steady)": "en-US-Chirp3-HD-Kore", "Charon (Deep)": "en-US-Chirp3-HD-Charon"}
with col2:
    st.write("##") # Spacing
    if st.button("🚫 STOP AUDIO", type="primary", use_container_width=True):
        st.session_state.audio_id += 1 # Forces player to reset
        st.session_state.audio_playing = False
        st.rerun()
with col3:
    st.write("##")
    if st.button("🗑️ CLEAR STORY", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio_id += 1
        st.rerun()

st.divider()

# --- 3. AUDIO ENGINE ---
def speak(text, label="Voice"):
    try:
        clean = re.sub(r'\*|_|#|>', '', text).strip()[:4800]
        input_tts = texttospeech.SynthesisInput(text=clean)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=v_map[v_choice])
        config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client_tts.synthesize_speech(input=input_tts, voice=voice, audio_config=config)
        b64 = base64.b64encode(response.audio_content).decode("utf-8")
        
        # Unique ID prevents the "double narration" overlap
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}" id="a_{st.session_state.audio_id}_{label}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"TTS Error: {e}")

# --- 4. CHAT & STREAMING ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What is your move?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        full_text = ""
        audio_sent = False
        
        # Start fresh audio ID for this turn
        st.session_state.audio_id += 1
        
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            full_text += chunk.text
            text_placeholder.markdown(full_text + "▌")
            
            # TRIGGER AFTER ~600 CHARS (Speed fix)
            if not audio_sent and len(full_text) > 600:
                audio_sent = True
                with st.status("Synthesizing Zephyr's voice..."):
                    speak(full_text, "Part1")
        
        text_placeholder.markdown(full_text)
        
        # Handle long story split
        if len(full_text) > 4800:
            mid = full_text.rfind('.', 0, 4800) + 1
            speak(full_text[mid:], "Part2")
        elif not audio_sent:
            speak(full_text, "Full")

    st.session_state.messages.append({"role": "assistant", "content": full_text})
