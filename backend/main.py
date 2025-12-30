import os
import json
import uuid
import traceback
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import spacy

# Import backend modules explicitly to avoid name collisions with repo-root files
from backend.cache_index import purge_older_than, add_entry, load_index
from backend.gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from backend.tts import synthesize_text_to_bytes

app = FastAPI()

# load spaCy model (raise helpful error if missing)
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise RuntimeError("Run: python -m spacy download en_core_web_sm") from e

# Determine repo root and frontend directory (allow common variants)
REPO_ROOT = Path(__file__).resolve().parents[1]
POSSIBLE_FRONTENDS = [
    REPO_ROOT / "frontend",
    REPO_ROOT / "fontend",         # tolerant for past misspelling
    REPO_ROOT / "frontend_build"
]

FRONTEND_DIR: Optional[Path] = None
for d in POSSIBLE_FRONTENDS:
    if d.exists():
        FRONTEND_DIR = d
        break

# Mount static assets on /static (so websocket upgrades are not routed to StaticFiles)
if FRONTEND_DIR:
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Serve the index.html explicitly at /
@app.get("/")
async def root():
    if FRONTEND_DIR:
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    return HTMLResponse(content="Frontend not found in container image.", status_code=404)


def split_into_sentences_spacy(text: str) -> List[str]:
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    out = []
    for s in sentences:
        if len(s) > 300:
            subs = s.split(",")
            out.extend([p.strip() + "," for p in subs[:-1]])
            out.append(subs[-1].strip())
        else:
            out.append(s)
    return out


@app.websocket("/ws/gm")
async def gm_ws(ws: WebSocket):
    # Instrumentation for Cloud Run logs
    try:
        print("WS: incoming connection - attempting accept")
        await ws.accept()
        print("WS: accepted connection")
    except Exception as e:
        print("WS: accept failed:", repr(e))
        traceback.print_exc()
        try:
            await ws.close()
        except Exception:
            pass
        return

    try:
        data = await ws.receive_text()
        print("WS: received initial text message len=", len(data) if data else 0)
        try:
            msg = json.loads(data)
        except Exception:
            await ws.send_text(json.dumps({"type": "error", "message": "Invalid JSON start message"}))
            await ws.close()
            print("WS: closed because start message not JSON")
            return

        if msg.get("type") != "start":
            await ws.send_text(json.dumps({"type": "error", "message": "First message must be type:'start' with 'history' array."}))
            await ws.close()
            print("WS: closed due to bad start message")
            return

        history = msg.get("history", [])
        recent_n = int(msg.get("recent_n", 5))
        target_words = int(msg.get("target_words", 800))
        voice_name = msg.get("voice_name", "en-US-Wavenet-D")
        audio_encoding = msg.get("audio_encoding", "WAV")
        speaking_rate = float(msg.get("speaking_rate", 1.0))

        print(f"WS: start message parsed: recent_n={recent_n}, target_words={target_words}, voice={voice_name}")

        memory_summary = summarize_history(history)
        await ws.send_text(json.dumps({"type": "memory_summary", "summary": memory_summary}))

        recent_entries = history[-recent_n:] if len(history) >= recent_n else history[:]
        user_msg = build_gm_user_message(memory_summary, recent_entries, target_words=target_words)

        # Stream generator returns text deltas
        await _stream_and_process(user_msg, ws, voice_name, audio_encoding, speaking_rate)

        # Signal done
        await ws.send_text(json.dumps({"type": "done"}))
        await ws.close()
        print("WS: finished normally and closed")
    except WebSocketDisconnect:
        print("WS: client disconnected")
        return
    except Exception as e:
        print("WS: exception in handler:", repr(e))
        traceback.print_exc()
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
            await ws.close()
        except Exception:
            pass
        return


async def _stream_and_process(user_msg: str, ws: WebSocket, voice_name: str, audio_encoding: str, speaking_rate: float):
    buffer = ""
    for delta in stream_chat_completion_messages(system_content="You are the GM LLM.", user_content=user_msg):
        buffer += delta
        sentences = split_into_sentences_spacy(buffer)
        complete = []
        incomplete = ""
        if sentences:
            if buffer.rstrip().endswith(('.', '?', '!', '…')):
                complete = sentences
                incomplete = ""
            else:
                if len(sentences) > 1:
                    complete = sentences[:-1]
                    incomplete = sentences[-1]
                else:
                    incomplete = sentences[0]
        else:
            incomplete = buffer

        if complete:
            for s in complete:
                # send text fragment
                try:
                    await ws.send_text(json.dumps({"type": "text_fragment", "fragment": s}))
                except Exception as e:
                    print("WS: failed to send text_fragment:", repr(e))

                # synthesize audio and send binary JSON-meta+audio payload the frontend can decode
                try:
                    audio_bytes = synthesize_text_to_bytes(s, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)

                    # Build JSON meta (UTF-8 bytes). Frontend will decode JSON meta.
                    meta = {
                        "id": str(uuid.uuid4()),
                        "encoding": audio_encoding,
                        "len": len(audio_bytes)
                    }
                    meta_bytes = json.dumps(meta).encode("utf-8")
                    header = len(meta_bytes).to_bytes(4, "big")
                    payload = header + meta_bytes + audio_bytes

                    # send binary frame
                    await ws.send_bytes(payload)
                    print(f"WS: sent binary audio id={meta['id']} len={len(audio_bytes)} meta_len={len(meta_bytes)}")
                except Exception as e:
                    print("WS: TTS/send error:", repr(e))
                    traceback.print_exc()
                    try:
                        await ws.send_text(json.dumps({"type": "error", "message": f"TTS error: {e}"}))
                    except Exception:
                        pass
            buffer = incomplete
    return
