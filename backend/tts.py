# backend/tts.py
import os
import hashlib
from typing import Tuple
from google.cloud import texttospeech, storage

CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
USE_GCS_CACHE = os.getenv("USE_GCS_CACHE", "true").lower() in ("1", "true", "yes")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")

tts_client = texttospeech.TextToSpeechClient()
gcs_client = storage.Client() if USE_GCS_CACHE and GCS_BUCKET else None

def _hash_key(text: str, voice_name: str, audio_encoding: str, speaking_rate: float) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(voice_name.encode("utf-8"))
    h.update(audio_encoding.encode("utf-8"))
    h.update(str(speaking_rate).encode("utf-8"))
    return h.hexdigest()

def _ssml_wrap_with_pauses(text: str) -> str:
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    esc = esc.replace("\n\n", "<break time='260ms'/>")
    esc = esc.replace("; ", "<break time='140ms'/>")
    esc = esc.replace(": ", "<break time='120ms'/>")
    esc = esc.replace(", ", ", <break time='80ms'/>")
    esc = esc.replace(". ", ". <break time='200ms'/>")
    esc = esc.replace("? ", "? <break time='200ms'/>")
    esc = esc.replace("! ", "! <break time='200ms'/>")
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
    key = _hash_key(text, voice_name, audio_encoding, speaking_rate)
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        gcs_bytes = _gcs_get_bytes(key)
        if gcs_bytes:
            return gcs_bytes

    filename = os.path.join(CACHE_DIR, f"{key}.{audio_encoding.lower()}")
    if os.path.exists(filename):
        with open(filename, "rb") as fh:
            data = fh.read()
            if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                _gcs_put_bytes(key, data)
            return data

    ssml_text = _ssml_wrap_with_pauses(text)
    input_speech = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=getattr(texttospeech.AudioEncoding, audio_encoding),
        speaking_rate=speaking_rate
    )
    response = tts_client.synthesize_speech(input=input_speech, voice=voice, audio_config=audio_config)
    audio_bytes = response.audio_content

    with open(filename, "wb") as fh:
        fh.write(audio_bytes)
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        _gcs_put_bytes(key, audio_bytes)
    return audio_bytes
