import os
import io
import hashlib
from typing import Optional
from google.cloud import texttospeech, storage
from cache_index import add_entry, purge_older_than, load_index

import wave
import time

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

# Default fallback voice (Google Cloud TTS)
FALLBACK_VOICE = "en-US-Wavenet-D"
SAMPLE_RATE = 24000  # Hz for WAV wrapper

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
    ssml = f"<speak>{esc}</speak>"
    return ssml

def _wrap_linear16_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE, channels: int = 1, sampwidth: int = 2) -> bytes:
    # pcm_bytes is expected to be raw 16-bit PCM (little endian)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)  # 2 bytes for 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def synthesize_text_to_bytes(text: str, voice_name: str = FALLBACK_VOICE, speaking_rate: float = 1.0, audio_encoding: str = "WAV", emotion: Optional[str] = None, cache_ttl_seconds: int = 60*60*24*7):
    """
    Synthesize text with Google Cloud TTS.
    Returns WAV bytes (LINEAR16 wrapped into WAV) so browsers decode reliably.
    If voice_name is invalid, retries with FALLBACK_VOICE.
    """
    key = _hash_key(text, voice_name, audio_encoding, speaking_rate, emotion)

    # Try GCS cache first
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        bucket = gcs_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"audio_cache/{key}.wav")
        if blob.exists():
            data = blob.download_as_bytes()
            return data

    local_path = os.path.join(CACHE_DIR, f"{key}.wav")
    if os.path.exists(local_path):
        return open(local_path, "rb").read()

    # Build the TTS request (Google)
    input_text = text
    # Use SSML if you want to preserve breaks; here we send plain text
    synthesis_input = texttospeech.SynthesisInput(text=input_text)

    # Map desired voice; Google expects e.g. 'en-US-Wavenet-D' as name
    voice_params = texttospeech.VoiceSelectionParams(
        name=voice_name,
        language_code=voice_name.split("-")[0] if "-" in voice_name else "en-US"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=speaking_rate,
        sample_rate_hertz=SAMPLE_RATE
    )

    # Try requested voice; on failure retry fallback
    try_voices = [voice_name]
    if voice_name != FALLBACK_VOICE:
        try_voices.append(FALLBACK_VOICE)

    last_exc = None
    for v in try_voices:
        try:
            if v != voice_name:
                voice_params.name = v
                # update language_code as well
                voice_params.language_code = v.split("-")[0] if "-" in v else "en-US"

            resp = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            pcm = resp.audio_content  # LINEAR16 raw PCM bytes
            wav_bytes = _wrap_linear16_to_wav(pcm, sample_rate=SAMPLE_RATE)
            # Save to local cache
            try:
                with open(local_path, "wb") as fh:
                    fh.write(wav_bytes)
                # Optionally upload to GCS
                if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                    bucket = gcs_client.bucket(GCS_BUCKET)
                    blob = bucket.blob(f"audio_cache/{key}.wav")
                    blob.upload_from_string(wav_bytes)
                    add_entry(key, len(wav_bytes))
            except Exception:
                pass
            return wav_bytes
        except Exception as e:
            last_exc = e
            # If it's a voice-related 400, try the fallback; otherwise continue to next try
            print(f"TTS attempt with voice={v} failed: {e}")
            continue

    # If we reach here, all attempts failed
    raise RuntimeError(f"TTS failed for voices {try_voices}: {last_exc}")
