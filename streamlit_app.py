import streamlit as st
import re
from google import genai
from google.cloud import texttospeech
import base64

# --- SETUP ---
st.set_page_config(page_title="Vexal TTRPG", layout="wide")
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# --- SIDEBAR (Character Sheet) ---
with st.sidebar:
    st.title("🧙‍♂️ Character Sheet")
    st.info("Health: 85/100 | Mana: 40/40")
    st.divider()
    st.write("**Inventory:** Healing Potion, Rusty Key")

# --- CORE LOGIC ---
def get_audio_base64(text):
    tts_client = texttospeech.TextToSpeechClient()
    # Limit to 5000 chars for API safety
    input_text = texttospeech.SynthesisInput(text=text[:4900])
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Journey-F")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    return base64.b64encode(response.audio_content).decode("utf-8")

# --- MAIN INTERFACE ---
st.title("🌌 The Vexal Engine")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 1. STREAM TEXT
        response_placeholder = st.empty()
        full_response = ""
        
        # We trigger Gemini
        stream = client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        for chunk in stream:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        
        # 2. GENERATE AUDIO (After text finishes, one single clear player)
        with st.spinner("Synthesizing narration..."):
            audio_b64 = get_audio_base64(full_response)
            audio_html = f'<audio autoplay src="data:audio/mp3;base64,{audio_b64}">'
            st.markdown(audio_html, unsafe_allow_html=True)
            st.audio(f"data:audio/mp3;base64,{audio_b64}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
