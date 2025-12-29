import os
import asyncio
import json
import re
import base64
import uuid
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from google.cloud import storage
from gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from tts import synthesize_text_to_bytes, USE_GCS_CACHE, GCS_BUCKET, CACHE_DIR

app = FastAPI()

# Serve frontend (assumes frontend/index.html at ../frontend/index.html)
@app.get("/")
async def root():
    return HTMLResponse(open("../frontend/index.html", "r", encoding="utf-8").read())

# Simple sentence splitter (same logic as earlier)
def split_into_sentences(text: str) -> List[str]:
    pieces = re.split(r'(?<=[\.\?\!\…]["\']?)\s+', text.strip())
    out = []
    for p in pieces:
        if len(p) > 250:
            sub = re.split(r'(?<=[,;])\s+', p)
            out.extend(sub)
        else:
            out.append(p)
    return [s.strip() for s in out if s.strip()]

# WebSocket endpoint: streams JSON messages + binary audio frames
@app.websocket("/ws/gm")
async def gm_ws(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_text()
        msg = json.loads(data)
        if msg.get("type") != "start":
            await ws.send_json({"type": "error", "message": "First message must be type:'start' with 'history' array."})
            await ws.close()
            return

        history = msg.get("history", [])
        recent_n = msg.get("recent_n", 5)
        target_words = int(msg.get("target_words", 800))
        voice_name = msg.get("voice_name", "en-US-AoedeNeural")
        audio_encoding = msg.get("audio_encoding", "OGG_OPUS")
        speaking_rate = float(msg.get("speaking_rate", 1.0))

        # 1) Summarize and send summary
        memory_summary = summarize_history(history)
        await ws.send_json({"type": "memory_summary", "summary": memory_summary})

        # 2) Build GM prompt
        recent_entries = history[-recent_n:] if len(history) >= recent_n else history[:]
        user_msg = build_gm_user_message(memory_summary, recent_entries, target_words=target_words)

        # 3) Stream LLM tokens; whenever we have complete sentence fragments, synthesize and send:
        buffer = ""
        async for delta in _stream_and_process(user_msg, ws, voice_name, audio_encoding, speaking_rate):
            pass

        await ws.send_json({"type": "done"})
        await ws.close()
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()

async def _stream_and_process(user_msg: str, ws: WebSocket, voice_name: str, audio_encoding: str, speaking_rate: float):
    buffer = ""
    for delta in stream_chat_completion_messages(system_content="You are the Game Master (GM) LLM for an ongoing interactive story. Preserve continuity and match style.", user_content=user_msg):
        buffer += delta
        sentences = split_into_sentences(buffer)
        complete = []
        incomplete = ""
        if sentences:
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
            # Send text fragment first for UI update
            await ws.send_json({"type": "text_fragment", "fragment": frag_text})
            # Synthesize audio fragment (may be cached)
            audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
            # Send JSON meta (id, bytes length, encoding) then send binary frame
            chunk_id = str(uuid.uuid4())
            meta = {"type": "audio_meta", "id": chunk_id, "length": len(audio_bytes), "encoding": audio_encoding}
            await ws.send_text(json.dumps(meta))
            # send raw binary bytes
            await ws.send_bytes(audio_bytes)
        buffer = incomplete
        await asyncio.sleep(0.01)
        yield

    # leftover buffer
    if buffer.strip():
        frag_text = buffer.strip()
        await ws.send_json({"type": "text_fragment", "fragment": frag_text})
        audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
        chunk_id = str(uuid.uuid4())
        meta = {"type": "audio_meta", "id": chunk_id, "length": len(audio_bytes), "encoding": audio_encoding}
        await ws.send_text(json.dumps(meta))
        await ws.send_bytes(audio_bytes)
    return

# --- Save / Load endpoints (store JSON/text saves in GCS or local disk) ---
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
    # Sanitize filename
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

@app.get("/list-saves")
async def list_saves():
    if bucket:
        blobs = bucket.list_blobs(prefix="saves/")
        names = [b.name.replace("saves/", "", 1) for b in blobs]
        return {"saves": names}
    else:
        path = os.path.join(CACHE_DIR, "saves")
        if not os.path.exists(path):
            return {"saves": []}
        names = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        return {"saves": names}

@app.get("/download-save/{name}")
async def download_save(name: str):
    safe_name = name.replace("..", "_")
    if bucket:
        blob = bucket.blob(f"saves/{safe_name}")
        if not blob.exists():
            raise HTTPException(status_code=404, detail="not found")
        data = blob.download_as_bytes()
        return StreamingResponse(iter([data]), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{safe_name}"'})
    else:
        path = os.path.join(CACHE_DIR, "saves", safe_name)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="not found")
        return StreamingResponse(iter([open(path, "rb").read()]), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{safe_name}"'})
