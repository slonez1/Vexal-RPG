# Replace the existing authentication block with this (keeps local st.secrets for dev,
# but prefers environment variable GEMINI_API_KEY for Cloud Run/Secret Manager).
import os
import streamlit as st
import re
import base64
from google.oauth2 import service_account
from google.cloud import texttospeech

# other imports remain as-is (genai import will be conditional below)
# --- 1. BOILERPLATE ---
st.set_page_config(page_title="Vexal RPG", layout="wide")
st.write("### 🚀 VEXAL ENGINE V3.0") # Visual check for update

# --- Authentication / credentials (works locally and on Cloud Run) ---
# Prefer GEMINI_API_KEY from environment (injected via Cloud Run --set-secrets),
# fall back to st.secrets for local development.
gemini_api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.warning("GEMINI_API_KEY not set in environment or st.secrets; LLM features will be disabled.")

# Google TTS: prefer Application Default Credentials (ADC) on Cloud Run.
# For local dev, keep existing st.secrets['gcp_service_account'] path.
if "gcp_service_account" in st.secrets:
    gcp_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(gcp_info)
    client_tts = texttospeech.TextToSpeechClient(credentials=creds)
else:
    # On Cloud Run, ADC (the service account) will be used automatically
    client_tts = texttospeech.TextToSpeechClient()

# Initialize Gemini/LLM client (try google.genai if available)
try:
    import google.genai as genai
    client_gemini = genai.Client(api_key=gemini_api_key) if gemini_api_key else None
except Exception:
    client_gemini = None

# --- The rest of the file remains unchanged; it uses client_tts and client_gemini ---
# (keep your existing speak(), UI, and chat loop below)
