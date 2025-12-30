# (full file — replace your existing backend/tts.py with this)
import os
import io
import hashlib
import traceback
from typing import Optional
from google.cloud import texttospeech, storage
# Import backend.cache_index explicitly to avoid shadowing by repo-root cache_index.py
from backend.cache_index import add_entry, purge_older_than, load_index

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
SAMPLE_RATE = 24000  # Hz used for LINEAR16/WAV wrapper

def _ssml_wrap(text: str, emotion: Optional[str] = None):
    # Minimal XML escape and inserted breaks
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
    # pcm_bytes expected raw LINEAR16 PCM (little endian). Wrap into a WAV container.
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)  # 2 bytes for 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def _generate_silence_wav(duration_ms: int = 150, sample_rate: int = SAMPLE_RATE, channels: int = 1, sampwidth: int = 2) -> bytes:
    # Generate a short silent WAV (PCM16) to return when TTS fails.
    frames = int(sample_rate * (duration_ms / 1000.0))
    pcm = (b'\x00' * frames * channels * sampwidth)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def synthesize_text_to_bytes(text: str, voice_name: str = FALLBACK_VOICE, speaking_rate: float = 1.0, audio_encoding: str = "WAV", emotion: Optional[str] = None, cache_ttl_seconds: int = 60*60*24*7):
    """
    Synthesize text with Google Cloud TTS. This implementation requests LINEAR16
    and always returns WAV bytes (LINEAR16 wrapped in WAV) so browsers can decode reliably.
    On any TTS error we log the traceback and return a short silent WAV to keep UX stable.
    """
    key = _hash_key(text, voice_name, audio_encoding, speaking_rate, emotion)
    # Try GCS cache first
    if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
        try:
            bucket = gcs_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"audio_cache/{key}.wav")
            if blob.exists():
                data = blob.download_as_bytes()
                return data
        except Exception:
            # don't fail on cache errors
            print("GCS cache check failed", traceback.format_exc())

    # Local cache file (.wav)
    filename = os.path.join(CACHE_DIR, f"{key}.wav")
    if os.path.exists(filename):
        try:
            data = open(filename, "rb").read()
            # Upload to GCS if configured (best-effort)
            if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                try:
                    bucket = gcs_client.bucket(GCS_BUCKET)
                    blob = bucket.blob(f"audio_cache/{key}.wav")
                    blob.upload_from_string(data)
                    add_entry(key, len(data))
                except Exception:
                    print("GCS upload failed", traceback.format_exc())
            return data
        except Exception:
            print("Local cache read failed", traceback.format_exc())

    ssml = _ssml_wrap(text, emotion)
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    # Use requested voice; fallback if invalid
    try_voices = [voice_name]
    if voice_name != FALLBACK_VOICE:
        try_voices.append(FALLBACK_VOICE)

    last_exc = None
    for v in try_voices:
        try:
            voice_params = texttospeech.VoiceSelectionParams(name=v, language_code=v.split("-")[0] if "-" in v else "en-US")
            # Request LINEAR16 so we can wrap to WAV (browser-friendly)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=speaking_rate,
                sample_rate_hertz=SAMPLE_RATE
            )

            resp = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            pcm = resp.audio_content  # raw LINEAR16 PCM bytes
            wav_bytes = _wrap_linear16_to_wav(pcm, sample_rate=SAMPLE_RATE)

            # Save to local cache (best-effort)
            try:
                with open(filename, "wb") as fh:
                    fh.write(wav_bytes)
                if USE_GCS_CACHE and gcs_client and GCS_BUCKET:
                    try:
                        bucket = gcs_client.bucket(GCS_BUCKET)
                        blob = bucket.blob(f"audio_cache/{key}.wav")
                        blob.upload_from_string(wav_bytes)
                        add_entry(key, len(wav_bytes))
                    except Exception:
                        print("GCS upload failed", traceback.format_exc())
            except Exception:
                print("Local cache write failed", traceback.format_exc())

            # Optionally purge older entries
            try:
                purge_older_than(cache_ttl_seconds)
            except Exception:
                print("purge_older_than failed", traceback.format_exc())

            return wav_bytes
        except Exception as e:
            last_exc = e
            print(f"TTS attempt with voice={v} failed: {repr(e)}")
            traceback.print_exc()
            # On any error, instead of raising to client, return a short silence WAV so playback continues
            try:
                return _generate_silence_wav(duration_ms=150, sample_rate=SAMPLE_RATE)
            except Exception:
                pass

    # If we exhausted attempts without returning, raise to signal failure
    raise RuntimeError(f"TTS failed for voices {try_voices}: {last_exc}")

def list_available_voices(language_code: Optional[str] = None):
    """
    Return a list of available voices. Each item contains:
      { name, language_codes, ssml_gender, natural_sample_rate_hertz }
    """
    try:
        if language_code:
            resp = tts_client.list_voices(language_code=language_code)
        else:
            resp = tts_client.list_voices()
        out = []
        for v in resp.voices:
            try:
                gender_name = texttospeech.SsmlVoiceGender(v.ssml_gender).name
            except Exception:
                gender_name = str(v.ssml_gender)
            out.append({
                "name": v.name,
                "language_codes": list(v.language_codes),
                "ssml_gender": gender_name,
                "natural_sample_rate_hertz": getattr(v, "natural_sample_rate_hertz", None)
            })
        return out
    except Exception:
        print("list_available_voices failed", traceback.format_exc())
        return []
