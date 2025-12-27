import streamlit as st
import google.generativeai as genai
from google.cloud import texttospeech
from google.oauth2 import service_account
import base64
import re

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Vexal RPG", layout="wide")

# Setup Gemini (Stable latest alias)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-latest')

# Setup Text-to-Speech
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

# --- 3. SIDEBAR DM PANEL ---
with st.sidebar:
    st.title("🧙‍♂️ Dungeon Master")
    
    voice_choice = st.selectbox(
        "Choose Narrator:",
        ["Zephyr (Bright Female)", "Kore (Steady Female)", "Charon (Smooth Male)"],
        index=0
    )
    
    voice_map = {
        "Zephyr (Bright Female)": "en-US-Chirp3-HD-Zephyr",
        "Kore (Steady Female)": "en-US-Chirp3-HD-Kore",
        "Charon (Smooth Male)": "en-US-Chirp3-HD-Charon"
    }
    selected_voice = voice_map[voice_choice]

    st.divider()
    
    # THE KILL SWITCH: Incrementing the key forces Streamlit to destroy old audio elements
    if st.button("🚫 STOP AUDIO", use_container_width=True, type="primary"):
        st.session_state.audio_key += 1
        st.rerun()

    if st.button("Clear Story History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio_key += 1
        st.rerun()

# --- 4. THE AUDIO ENGINE ---
def get_audio_html(text, label=""):
    # If the stop button was pressed, this audio element will have a new key and be 'reset'
    try:
        clean_text = re.sub(r'\*|_|#|>', '', text).strip()[:4800]
        input_text = texttospeech.SynthesisInput(text=clean_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=selected_voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client_tts.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        
        # Unique ID based on audio_key allows us to "kill" it from the sidebar
        st.write(f"🔊 {label} Loaded")
        st.markdown(
            f'<audio autoplay src="data:audio/mp3;base64,{audio_b64}" id="v_{st.session_state.audio_key}_{label.replace(" ","")}">', 
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 5. MAIN CHAT ---
st.title("🌌 The Vexal Chronicles")

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Action
if prompt := st.chat_input("Enter your command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        audio_triggered = False
        
        # Text Generation (Streaming)
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
            
            # FAST START: Trigger voice after ~800 chars (approx 1st paragraph)
            if not audio_triggered and len(full_response) > 800:
                audio_triggered = True
                with st.sidebar:
                    st.info(f"🎙️ {voice_choice.split(' ')[0]} is speaking...")
                    get_audio_html(full_response, "Part I")
        
        response_placeholder.markdown(full_response)
        
        # SECOND HALF: Trigger if the story is a 1,200-word epic
        if len(full_response) > 4800:
            mid = full_response.rfind('.', 0, 4800) + 1
            get_audio_html(full_response[mid:], "Part II")
        elif not audio_triggered:
            # Fallback for short responses that never hit 800 chars
            get_audio_html(full_response, "Full Narration")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
