import streamlit as st
import re
import base64
from google import genai
from google.cloud import texttospeech
from google.oauth2 import service_account

# --- 1. SETTINGS & AUTH ---
st.set_page_config(page_title="Vexal RPG", layout="wide")

# Build credentials from Streamlit Secrets
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
client_tts = texttospeech.TextToSpeechClient(credentials=creds)

# Fixed Client Initialization to avoid the 404 error
client_gemini = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"],
    http_options={'api_version': 'v1'}
)

# --- 2. SESSION STATE (The Game Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stats" not in st.session_state:
    st.session_state.stats = {"Health": 100, "Mana": 50, "Gold": 10}
if "inventory" not in st.session_state:
    st.session_state.inventory = ["Rusty Dagger", "Ancient Map"]

# --- 3. THE SIDEBAR ---
with st.sidebar:
    st.title("🧙‍♂️ Character")
    st.metric("Health", f"{st.session_state.stats['Health']}%")
    st.metric("Mana", f"{st.session_state.stats['Mana']}%")
    st.divider()
    st.write("**Inventory:**")
    for item in st.session_state.inventory:
        st.write(f"• {item}")
    
    if st.button("New Game"):
        st.session_state.messages = []
        st.rerun()

# --- 4. AUDIO ENGINE ---
def get_audio_html(text, label=""):
    try:
        # Clean markdown characters for the voice engine
        clean_text = re.sub(r'\*|_|#|>', '', text).strip()
        
        input_text = texttospeech.SynthesisInput(text=clean_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            name="en-US-Journey-F"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3, 
            speaking_rate=1.05
        )
        
        response = client_tts.synthesize_speech(
            input=input_text, 
            voice=voice, 
            audio_config=audio_config
        )
        
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        st.write(f"🔊 {label} Audio Loaded")
        st.audio(f"data:audio/mp3;base64,{audio_b64}")
        
    except Exception as e:
        st.error(f"Narration Error: {e}")

# --- 5. MAIN CHAT INTERFACE ---
st.title("🌌 The Vexal Chronicles")

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Using the most stable model name
        stream = client_gemini.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"max_output_tokens": 2500}
        )
        
        for chunk in stream:
            full_response += chunk.text
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        
        # --- AUTOMATIC NARRATION SEGMENTS ---
        with st.status("Vexal Voice Manifesting..."):
            # Split to handle Google's 5000 char limit
            if len(full_response) > 4800:
                # Part 1: Start to midpoint
                mid = full_response.rfind('.', 0, 4800) + 1
                get_audio_html(full_response[:mid], "Part I")
                # Part 2: Midpoint to end
                get_audio_html(full_response[mid:], "Part II")
            else:
                get_audio_html(full_response, "Full Narration")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
