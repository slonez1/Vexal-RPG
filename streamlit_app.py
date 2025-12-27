import streamlit as st
import google.generativeai as genai
from google.cloud import texttospeech
from google.oauth2 import service_account
import base64
import re

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Vexal RPG", layout="wide")

# Setup Gemini (Stable Library)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Setup Text-to-Speech
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🧙‍♂️ Vexal RPG")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# --- 4. AUDIO FUNCTION ---
def get_audio_html(text, label=""):
    try:
        clean_text = re.sub(r'\*|_|#|>', '', text).strip()[:4800]
        input_text = texttospeech.SynthesisInput(text=clean_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Journey-F")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client_tts.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        st.write(f"🔊 {label} Ready")
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{audio_b64}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# --- 5. CHAT ---
st.title("🌌 The Vexal Chronicles")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # This is the most stable streaming method available
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        
        # Automatic Audio
        with st.spinner("Vexal voice manifesting..."):
            if len(full_response) > 4800:
                mid = full_response.rfind('.', 0, 4800) + 1
                get_audio_html(full_response[:mid], "Part I")
                get_audio_html(full_response[mid:], "Part II")
            else:
                get_audio_html(full_response, "Full Narration")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
