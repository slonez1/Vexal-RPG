import os
import asyncio
import json
import struct
import uuid
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import spacy
import cbor2

from gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from tts import synthesize_text_to_bytes
from cache_index import purge_older_than, add_entry

app = FastAPI()
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise RuntimeError("Run: python -m spacy download en_core_web_sm") from e

@app.get("/")
async def root():
    return HTMLResponse(open("../frontend/index.html", "r", encoding="utf-8").read())

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
                    # might be growing fragment
                    if len(sentences[0]) > min_fragment_chars:
                        # make small fragment to reduce latency
                        complete = [sentences[0]]
                        incomplete = ""
                    else:
                        incomplete = sentences[0]
        else:
            incomplete = buffer

        for frag in complete:
            frag_text = frag.strip()
            if not frag_text:
                continue
            await ws.send_text(json.dumps({"type":"text_fragment","fragment":frag_text}))
            # infer emotion from memory_summary? For now, a simple heuristic:
            emotion = None
            if "angry" in frag_text.lower() or "yelled" in frag_text.lower():
                emotion = "agitated"
            # synthesize
            audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding, emotion=emotion)
            # Build CBOR meta
            meta = {"id": str(uuid.uuid4()), "encoding": audio_encoding, "length": len(audio_bytes)}
            meta_bytes = cbor2.dumps(meta)
            header = struct.pack(">I", len(meta_bytes))
            # single binary frame: header + meta + audio
            await ws.send_bytes(header + meta_bytes + audio_bytes)
        buffer = incomplete
        await asyncio.sleep(0.01)
        yield

    # leftover
    if buffer.strip():
        frag_text = buffer.strip()
        await ws.send_text(json.dumps({"type":"text_fragment","fragment":frag_text}))
        audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
        meta = {"id": str(uuid.uuid4()), "encoding": audio_encoding, "length": len(audio_bytes)}
        meta_bytes = cbor2.dumps(meta)
        header = struct.pack(">I", len(meta_bytes))
        await ws.send_bytes(header + meta_bytes + audio_bytes)
    return
