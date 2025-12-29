# backend/main.py
import os
import asyncio
import json
import re
import struct
import uuid
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from google.cloud import storage
import spacy

from gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from tts import synthesize_text_to_bytes, USE_GCS_CACHE, GCS_BUCKET, CACHE_DIR

app = FastAPI()

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    # Helpful error if model missing
    raise RuntimeError("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm") from e

@app.get("/")
async def root():
    return HTMLResponse(open("../frontend/index.html", "r", encoding="utf-8").read())

def split_into_sentences_spacy(text: str) -> List[str]:
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    # If a sentence is too long (>300 chars), split at commas/semicolons
    out = []
    for s in sentences:
        if len(s) > 300:
            sub = re.split(r'(?<=[,;])\s+', s)
            out.extend([p.strip() for p in sub if p.strip()])
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
        recent_n = msg.get("recent_n", 5)
        target_words = int(msg.get("target_words", 800))
        voice_name = msg.get("voice_name", "en-US-AoedeNeural")
        audio_encoding = msg.get("audio_encoding", "OGG_OPUS")
        speaking_rate = float(msg.get("speaking_rate", 1.0))

        # 1) Summarize and send summary (text frame)
        memory_summary = summarize_history(history)
        await ws.send_text(json.dumps({"type": "memory_summary", "summary": memory_summary}))

        # 2) Build GM prompt and stream LLM output
        recent_entries = history[-recent_n:] if len(history) >= recent_n else history[:]
        user_msg = build_gm_user_message(memory_summary, recent_entries, target_words=target_words)

        buffer = ""
        # stream deltas
        async for _ in _stream_and_process(user_msg, ws, voice_name, audio_encoding, speaking_rate):
            pass

        await ws.send_text(json.dumps({"type": "done"}))
        await ws.close()
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        await ws.close()

async def _stream_and_process(user_msg: str, ws: WebSocket, voice_name: str, audio_encoding: str, speaking_rate: float):
    buffer = ""
    for delta in stream_chat_completion_messages(system_content="You are the Game Master (GM) LLM for an ongoing interactive story. Preserve continuity and match style.", user_content=user_msg):
        buffer += delta
        # use spaCy to split; keep last incomplete sentence in buffer
        sentences = split_into_sentences_spacy(buffer)
        complete = []
        incomplete = ""
        if sentences:
            # If buffer ends with sentence punctuation, all sentences are complete
            if re.search(r'[\.\?\!\…]["\']?\s*$', buffer):
                complete = sentences
                incomplete = ""
            else:
                if len(sentences) > 1:
                    complete = sentences[:-1]
                    incomplete = sentences[-1]
                else:
                    complete = []
                    incomplete = sentences[0]
        else:
            incomplete = buffer

        for frag in complete:
            frag_text = frag.strip()
            if not frag_text:
                continue
            # Send text fragment (so UI can show it)
            await ws.send_text(json.dumps({"type": "text_fragment", "fragment": frag_text}))
            # Synthesize audio (may be cached)
            audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
            # Build metadata
            meta = {"type":"audio", "id": str(uuid.uuid4()), "encoding": audio_encoding, "length": len(audio_bytes)}
            meta_bytes = json.dumps(meta).encode("utf-8")
            header = struct.pack(">I", len(meta_bytes))  # 4-byte big-endian length
            # send binary frame containing header + meta_bytes + audio_bytes
            await ws.send_bytes(header + meta_bytes + audio_bytes)
        buffer = incomplete
        await asyncio.sleep(0.01)
        yield

    # leftover
    if buffer.strip():
        frag_text = buffer.strip()
        await ws.send_text(json.dumps({"type": "text_fragment", "fragment": frag_text}))
        audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
        meta = {"type":"audio", "id": str(uuid.uuid4()), "encoding": audio_encoding, "length": len(audio_bytes)}
        meta_bytes = json.dumps(meta).encode("utf-8")
        header = struct.pack(">I", len(meta_bytes))
        await ws.send_bytes(header + meta_bytes + audio_bytes)
    return

# Save/load endpoints (same as previous)
if USE_GCS_CACHE and GCS_BUCKET:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
else:
    storage_client = None
    bucket = None

@app.post("/save")
async def save_game(request: Request):
    payload = await request.json()
    filename = payload.get("filename")
    content = payload.get("content")
    if not filename or content is None:
        raise HTTPException(status_code=400, detail="filename and content required")
    safe_name = filename.replace("..", "_")
    if bucket:
        blob = bucket.blob(f"saves/{safe_name}")
        blob.upload_from_string(content)
        return {"status": "ok", "path": f"gs://{GCS_BUCKET}/saves/{safe_name}"}
    else:
        path = os.path.join(CACHE_DIR, "saves")
        os.makedirs(path, exist_ok=True)
        local_path = os.path.join(path, safe_name)
        with open(local_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return {"status": "ok", "path": local_path}
