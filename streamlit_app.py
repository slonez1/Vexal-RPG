import streamlit as st
import re
import base64
from google import genai
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. AUTHENTICATION ---
# We build the credentials object directly from your Streamlit Secrets
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)
client_gemini = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. GAME STATE (The "Memory") ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stats" not in st.session_state:
    st.session_state.stats = {"Health": 100, "Mana": 50, "Gold": 10}
if "inventory" not in st.session_state:
    st.session_state.inventory = ["Rusty Dagger", "Leather Armor"]

# --- 3. THE SIDEBAR (Character Sheet) ---
with st.sidebar:
    st.title("🧙‍♂️ Vexal Explorer")
    st.metric("HP", f"{st.session_state.stats['Health']}/100")
    st.metric("Mana", f"{st.session_state.stats['Mana']}/50")
    st.divider()
    st.write("**Backpack:**")
    for item in st.session_state.inventory:
        st.write(f"• {item}")
    
    if st.button("Reset Game"):
        st.session_state.messages = []
        st.rerun()

# --- 4. AUDIO FUNCTION ---
def get_audio_html(text, label="VEXAL"):
    try:
        # Google's limit is 5000, so we pass only what's requested
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Journey-F")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=1.0)
        
        response = client_tts.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        
        # We display the player. The first one will 'autoplay'.
        st.write(f"🔊 {label} Audio Ready")
        st.audio(f"data:audio/mp3;base64,{audio_b64}")
    except Exception as e:
        st.error(f"Audio Error: {e}")

# --- 5. MAIN INTERFACE ---
st.title("🌌 The Vexal Chronicles")
st.caption("A high-fidelity AI TTRPG experience")

# Display historical messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Action
if prompt := st.chat_input("What is your next move?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        audio_triggered = False  # Track if we've started the voice yet
        
        stream = client_gemini.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        for chunk in stream:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
            
            # FAST TRIGGER: Start audio once we have ~3 paragraphs (approx 1000 chars)
            if not audio_triggered and len(full_response) > 1000:
                audio_triggered = True
                with st.spinner("Vexal voice manifesting..."):
                    audio_html = get_audio_html(full_response) # Narrates the "Intro"
                    st.markdown(audio_html, unsafe_allow_html=True)
        
        response_placeholder.markdown(full_response)
        
        # If the story was very short, trigger audio at the end
        if not audio_triggered:
            audio_html = get_audio_html(full_response)
            st.markdown(audio_html, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
