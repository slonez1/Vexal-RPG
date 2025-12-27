import streamlit as st
import google.generativeai as genai
from google.cloud import texttospeech
from google.oauth2 import service_account
import base64
import re

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Vexal RPG", layout="wide")

# Setup Gemini (Using the stable 'latest' alias)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-latest')

# Setup Text-to-Speech
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🧙‍♂️ Dungeon Master")
    
    # VOICE SELECTOR
    voice_choice = st.selectbox(
        "Choose Narrator:",
        ["Zephyr (Bright Female)", "Kore (Steady Female)", "Charon (Smooth Male)"],
        index=0
    )
    
    # Map the choice to the actual Google Voice Name
    voice_map = {
        "Zephyr (Bright Female)": "en-US-Chirp3-HD-Zephyr",
        "Kore (Steady Female)": "en-US-Chirp3-HD-Kore",
        "Charon (Smooth Male)": "en-US-Chirp3-HD-Charon"
    }
    selected_voice = voice_map[voice_choice]

    with st.sidebar:
    st.title("🧙‍♂️ Dungeon Master")
    
    # ... (Voice Selector code stays the same) ...

    st.divider()
    # THE KILL SWITCH
    if st.button("🚫 STOP AUDIO", use_container_width=True):
        st.session_state.audio_key += 1  # Changing the key forces the audio player to vanish
        st.rerun()

    if st.button("Reset Story", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio_key += 1
        st.rerun()

# --- 3. THE "SPEEDY" AUDIO FUNCTION ---
def get_audio_html(text, label=""):
    # We add a unique key based on the session state
    # When st.session_state.audio_key changes, this whole block is destroyed
    audio_container = st.container()
    with audio_container:
        try:
            clean_text = re.sub(r'\*|_|#|>', '', text).strip()[:4800]
            input_text = texttospeech.SynthesisInput(text=clean_text)
            voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=selected_voice)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            
            response = client_tts.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
            audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
            
            st.write(f"🔊 {label} Ready")
            # The 'key' ensures Streamlit can track and kill this specific element
            st.markdown(
                f'<audio autoplay src="data:audio/mp3;base64,{audio_b64}" id="audio_{st.session_state.audio_key}">', 
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Audio Error: {e}")

# --- 4. MAIN INTERFACE ---
st.title("🌌 The Vexal Chronicles")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What is your next move?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        audio_triggered = False
        
        # STREAMING TEXT
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
            
            # THE SPEED FIX: Trigger Part 1 as soon as we have ~800 characters (approx 1 paragraph)
            if not audio_triggered and len(full_response) > 800:
                audio_triggered = True
                with st.spinner(f"{voice_choice.split(' ')[0]} is manifesting..."):
                    get_audio_html(full_response, "Part I")
        
        response_placeholder.markdown(full_response)
        
        # Part 2: Handle the rest of the 1200 words
        if len(full_response) > 4800:
            mid = full_response.rfind('.', 0, 4800) + 1
            get_audio_html(full_response[mid:], "Part II")
        elif not audio_triggered:
            get_audio_html(full_response, "Full Narration")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
