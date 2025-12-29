import os
import hashlib
from typing import Optional
from google.cloud import texttospeech, storage
from cache_index import add_entry, purge_older_than, load_index

CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
USE_GCS_CACHE = os.getenv("USE_GCS_CACHE", "false").lower() in ("1", "true", "yes")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")

tts_client = texttospeech.TextToSpeechClient()
gcs_client = storage.Client() if USE_GCS_CACHE and GCS_BUCKET else None

def _hash_key(text: str, voice_name: str, audio_encoding: str, speaking_rate: float, emotion: Optional[str]):
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(voice_name.encode("utf-8"))
    h.update(audio_encoding.encode("utf-8"))
    h.update(str(speaking_rate).encode("utf-8"))
    h.update(str(emotion or "").encode("utf-8"))
    return h.hexdigest()

# Emotion -> prosody presets (speaker_rate multiplier and prosody attrs)
EMOTION_PRESETS = {
    "neutral": {"rate": "0.98"},
    "calm": {"rate": "0.95"},
    "agitated": {"rate": "1.05"},
    "sad": {"rate": "0.92"},
    "joyful": {"rate": "1.08"},
    "urgent": {"rate": "1.12", "pitch": "+2%"}
}

def _ssml_wrap(text: str, emotion: Optional[str] = None):
    # Minimal XML escape
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    esc = esc.replace("\n\n", "<break time='260ms'/>")
    esc = esc.replace("; ", "<break time='140ms'/>")
    esc = esc.replace(": ", "<break time='120ms'/>")
    esc = esc.replace(", ", ", <break time='80ms'/>")
    esc = esc.replace(". ", ". <break time='200ms'/>")
    esc = esc.replace("? ", "? <break time='200ms'/>")
    esc = esc.replace("! ", "! <break time='200ms'/>")
    preset = EMOTION_PRESETS.get(emotion, EMOTION_PRESETS["neutral"])
    prosody_attrs = f"rate='{preset.get('rate', '0.98')}'"
    if "pitch" in preset:
        prosody_attrs += f" pitch='{preset['pitch']}'"
    ssml = f"<speak><prosody {prosody_attrs}>{esc}</prosody></speak>"
    return ssml

def synthesize_text_to_bytes(text: str, voice_name: str = "en-US-AoedeNeural", speaking_rate: float = 1.0, audio_encoding: str = "OGG_OPUS", emotion: Optional[str] = None, cache_ttl_seconds: int = 60*60*24*7):
    key = _hash_key(text, voice_name, audio_encoding, speaking_rate, emotion)
    # Try GCS
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"audio_cache/{key}")
        if blob.exists():
            data = blob.download_as_bytes()
            return data
    # Local cache file
    filename = os.path.join(CACHE_DIR, f"{key}.{audio_encoding.lower()}")
    if os.path.exists(filename):
        with open(filename, "rb") as fh:
            data = fh.read()
            # Upload to GCS if configured
            if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                bucket = gcs_client.bucket(GCS_BUCKET)
                blob = bucket.blob(f"audio_cache/{key}")
                blob.upload_from_string(data)
                add_entry(key, len(data))
            return data

    ssml = _ssml_wrap(text, emotion)
    input_speech = texttospeech.SynthesisInput(ssml=ssml)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=getattr(texttospeech.AudioEncoding, audio_encoding), speaking_rate=speaking_rate)
    resp = tts_client.synthesize_speech(input=input_speech, voice=voice, audio_config=audio_config)
    data = resp.audio_content
    # cache locally
    with open(filename, "wb") as fh:
        fh.write(data)
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"audio_cache/{key}")
        blob.upload_from_string(data)
        add_entry(key, len(data))
    # Optionally purge older entries
    purge_older_than(cache_ttl_seconds)
    return data
