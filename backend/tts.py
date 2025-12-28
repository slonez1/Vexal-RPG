import os
import hashlib
from typing import Tuple
from google.cloud import texttospeech

# Configure client via GOOGLE_APPLICATION_CREDENTIALS env var (recommended)
client = texttospeech.TextToSpeechClient()

# Simple on-disk cache directory
CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _hash_key(text: str, voice_name: str, audio_encoding: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(voice_name.encode("utf-8"))
    h.update(audio_encoding.encode("utf-8"))
    return h.hexdigest()

def synthesize_text_to_bytes(text: str, voice_name: str = "en-US-AoedeNeural", speaking_rate: float = 1.0, audio_encoding="OGG_OPUS") -> bytes:
    """
    Synthesize `text` using Google Cloud TTS. Returns raw audio bytes (OGG/MP3/LINEAR16 depending on audio_encoding).
    Caches audio files on disk keyed by hash(text+voice+encoding).
    """
    key = _hash_key(text, voice_name, audio_encoding)
    filename = os.path.join(CACHE_DIR, f"{key}.{audio_encoding.lower()}")
    if os.path.exists(filename):
        with open(filename, "rb") as fh:
            return fh.read()

    # Build request
    # We send plain text; for more control, wrap in SSML.
    input_text = texttospeech.SynthesisInput(text=text)
    # Default language_code en-US; voice_name can be "en-US-AoedeNeural" or similar
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=getattr(texttospeech.AudioEncoding, audio_encoding),
        speaking_rate=speaking_rate
    )
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    audio_bytes = response.audio_content
    # Cache to disk
    with open(filename, "wb") as fh:
        fh.write(audio_bytes)
    return audio_bytes
