import os
import asyncio
import json
import struct
import uuid
from typing import List
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import spacy
import cbor2

from gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from tts import synthesize_text_to_bytes
from cache_index import purge_older_than, add_entry

app = FastAPI()

# Try to load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise RuntimeError("Run: python -m spacy download en_core_web_sm") from e

# Mount frontend static files if present in the container image
# backend/ is at repo_root/backend so repo root is two levels up from this file
REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
if FRONTEND_DIR.exists():
    # Mount the frontend directory at root, with html=True so index.html is served
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return HTMLResponse(content="Frontend not found in container image.", status_code=404)


def split_into_sentences_spacy(text: str) -> List[str]:
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    # split very long sentences at commas if needed
    out = []
    for s in sentences:
        if len(s) > 300:
            subs = s.split(",")
            out.extend([p.strip()+"," for p in subs[:-1]])
            out.append(subs[-1].strip())
        else:
            out.append(s)
    return out

@app.websocket("/ws/gm")
async def gm_ws(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_text()
        msg = json.loads(data)
        if msg.get("type") != "start":
            await ws.send_text(json.dumps({"type": "error", "message": "First message must be type:'start' with 'history' array."}))
            await ws.close()
            return

        history = msg.get("history", [])
        recent_n = int(msg.get("recent_n", 5))
        target_words = int(msg.get("target_words", 800))
        voice_name = msg.get("voice_name", "en-US-AoedeNeural")
        audio_encoding = msg.get("audio_encoding", "OGG_OPUS")
        speaking_rate = float(msg.get("speaking_rate", 1.0))

        memory_summary = summarize_history(history)
        await ws.send_text(json.dumps({"type":"memory_summary","summary":memory_summary}))

        recent_entries = history[-recent_n:] if len(history) >= recent_n else history[:]
        user_msg = build_gm_user_message(memory_summary, recent_entries, target_words=target_words)

        buffer = ""
        async for _ in _stream_and_process(user_msg, ws, voice_name, audio_encoding, speaking_rate):
            pass

        await ws.send_text(json.dumps({"type":"done"}))
        await ws.close()
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_text(json.dumps({"type":"error", "message": str(e)}))
        await ws.close()

async def _stream_and_process(user_msg: str, ws: WebSocket, voice_name: str, audio_encoding: str, speaking_rate: float):
    buffer = ""
    min_fragment_chars = 40  # allow small fragments; tune for latency
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
            # process/send audio for each complete sentence (existing code continues)
            for s in complete:
                # send text fragment
                await ws.send_text(json.dumps({"type":"text","text":s}))
                # synthesize audio bytes and send as CBOR or appropriate streaming (existing impl)
                try:
                    audio_bytes = synthesize_text_to_bytes(s, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
                    # send audio as base64 or chunked—existing app logic expected CBOR streaming; keep existing approach
                    await ws.send_text(json.dumps({"type":"audio","len":len(audio_bytes)}))
                except Exception as e:
                    await ws.send_text(json.dumps({"type":"error","message":f"TTS error: {e}"}))
            buffer = incomplete
    return
