import os
import hashlib
from typing import Tuple
from google.cloud import texttospeech, storage

# Configure cache
CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
USE_GCS_CACHE = os.getenv("USE_GCS_CACHE", "true").lower() in ("1", "true", "yes")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")

# Clients
tts_client = texttospeech.TextToSpeechClient()
gcs_client = storage.Client() if USE_GCS_CACHE and GCS_BUCKET else None

def _hash_key(text: str, voice_name: str, audio_encoding: str, speaking_rate: float) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(voice_name.encode("utf-8"))
    h.update(audio_encoding.encode("utf-8"))
    h.update(str(speaking_rate).encode("utf-8"))
    return h.hexdigest()

def _ssml_wrap_with_pauses(text: str) -> str:
    """
    Simple heuristics to insert short SSML breaks/pauses and prosody around punctuation.
    - Commas -> short breaks
    - Semicolons/colons -> medium breaks
    - Double newlines -> paragraph break (longer)
    - Wrap final in <speak> and <prosody>
    """
    # Escape XML-sensitive characters minimally
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Insert breaks
    esc = esc.replace("\n\n", "<break time='260ms'/>")
    esc = esc.replace("; ", "<break time='140ms'/>")
    esc = esc.replace(": ", "<break time='120ms'/>")
    esc = esc.replace(", ", ", <break time='80ms'/>")
    # Add a small pause after sentence-ending punctuation if not present
    esc = esc.replace(". ", ". <break time='200ms'/>")
    esc = esc.replace("? ", "? <break time='200ms'/>")
    esc = esc.replace("! ", "! <break time='200ms'/>")
    # Wrap in speak + prosody with slightly lowered rate for naturalness
    ssml = f"<speak><prosody rate='0.98'>{esc}</prosody></speak>"
    return ssml

def _gcs_get_bytes(key: str) -> bytes | None:
    if not gcs_client or not GCS_BUCKET:
        return None
    bucket = gcs_client.bucket(GCS_BUCKET)
    blob = bucket.blob(f"audio_cache/{key}")
    if blob.exists():
        return blob.download_as_bytes()
    return None

def _gcs_put_bytes(key: str, data: bytes):
    if not gcs_client or not GCS_BUCKET:
        return
    bucket = gcs_client.bucket(GCS_BUCKET)
    blob = bucket.blob(f"audio_cache/{key}")
    blob.upload_from_string(data)

def synthesize_text_to_bytes(text: str, voice_name: str = "en-US-AoedeNeural", speaking_rate: float = 1.0, audio_encoding: str = "OGG_OPUS") -> bytes:
    """
    Synthesize text with SSML heuristics. Uses GCS cache if enabled; otherwise local disk cache.
    Returns raw audio bytes (format depends on audio_encoding).
    """
    key = _hash_key(text, voice_name, audio_encoding, speaking_rate)
    # Try GCS cache
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        gcs_bytes = _gcs_get_bytes(key)
        if gcs_bytes:
            return gcs_bytes

    # Local disk cache fallback
    filename = os.path.join(CACHE_DIR, f"{key}.{audio_encoding.lower()}")
    if os.path.exists(filename):
        with open(filename, "rb") as fh:
            data = fh.read()
            # Upload to GCS if configured and not present there yet
            if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                _gcs_put_bytes(key, data)
            return data

    # Build SSML
    ssml_text = _ssml_wrap_with_pauses(text)
    input_speech = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=getattr(texttospeech.AudioEncoding, audio_encoding),
        speaking_rate=speaking_rate
    )
    response = tts_client.synthesize_speech(input=input_speech, voice=voice, audio_config=audio_config)
    audio_bytes = response.audio_content

    # Cache locally
    with open(filename, "wb") as fh:
        fh.write(audio_bytes)
    # Optionally upload to GCS
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        _gcs_put_bytes(key, audio_bytes)
    return audio_bytes
