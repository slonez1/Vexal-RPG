import os
import asyncio
import base64
import json
import re
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from gm_orchestrator_stream import summarize_history, build_gm_user_message, stream_chat_completion_messages
from tts import synthesize_text_to_bytes

app = FastAPI()

# Serve simple demo front-end (see frontend/index.html later)
@app.get("/")
async def root():
    return HTMLResponse(open("../frontend/index.html", "r", encoding="utf-8").read())

# Utility: simple sentence splitter — tries to produce reasonably-sized chunks (keeps abbreviations naive)
SENTENCE_END_RE = re.compile(r'([^\n]{40,}?[\.\?\!…]["\']?\s+)|([^\n]{120,}[\s])', re.DOTALL)

def split_into_sentences(text: str) -> List[str]:
    # Very naive splitter: split on punctuation followed by whitespace; keep small fragments together.
    pieces = re.split(r'(?<=[\.\?\!\…]["\']?)\s+', text.strip())
    # If any piece is too long (e.g., > 200 chars) try to break it at comma/semicolon positions
    out = []
    for p in pieces:
        if len(p) > 250:
            sub = re.split(r'(?<=[,;])\s+', p)
            out.extend(sub)
        else:
            out.append(p)
    return [s.strip() for s in out if s.strip()]

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

        # 1) Summarize history synchronously and send to client
        memory_summary = summarize_history(history)
        await ws.send_json({"type": "memory_summary", "summary": memory_summary})

        # 2) Build GM prompt and stream LLM output
        recent_entries = history[-recent_n:] if len(history) >= recent_n else history[:]
        user_msg = build_gm_user_message(memory_summary, recent_entries, target_words=target_words)

        # We'll collect incremental text; whenever we detect sentence boundaries, synthesize that fragment
        text_buffer = ""
        sentence_buffer = []

        async for delta in _stream_and_process(user_msg, ws, voice_name, audio_encoding, speaking_rate):
            # loop inside helper
            pass

        # After completion, send a final 'done' message
        await ws.send_json({"type": "done"})
        await ws.close()
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()

async def _stream_and_process(user_msg: str, ws: WebSocket, voice_name: str, audio_encoding: str, speaking_rate: float):
    """
    Helper that iterates over streaming LLM output, chunks text into sentences/fragments,
    synthesizes each fragment and sends both text_fragment and audio_chunk messages to the WS client.
    """
    buffer = ""
    # iterate over incremental text deltas from the LLM
    for delta in stream_chat_completion_messages(system_content="You are the Game Master (GM) LLM for an ongoing interactive story. Preserve continuity and match style.", user_content=user_msg):
        buffer += delta
        # If buffer contains one or more "complete" sentences, extract them
        sentences = split_into_sentences(buffer)
        # Keep last sentence as possibly incomplete (if no punctuation at end)
        complete = []
        incomplete = ""
        if sentences:
            # If the last character of buffer ends in sentence-terminating punctuation, all are complete
            if re.search(r'[\.\?\!\…]["\']?\s*$', buffer):
                complete = sentences
                incomplete = ""
            else:
                if len(sentences) > 1:
                    complete = sentences[:-1]
                    incomplete = sentences[-1]
                else:
                    # no complete sentences yet
                    complete = []
                    incomplete = sentences[0]
        else:
            incomplete = buffer

        # For each complete sentence fragment, synthesize & send
        for frag in complete:
            frag_text = frag.strip()
            if not frag_text:
                continue
            # Send text fragment first so client can display
            await ws.send_json({"type": "text_fragment", "fragment": frag_text})
            # Synthesize audio for fragment (may be cached)
            audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            await ws.send_json({"type": "audio_chunk", "audio_b64": b64, "audio_encoding": audio_encoding})
        # Set buffer to incomplete remainder
        buffer = incomplete

        # Yield control to event loop to avoid blocking
        await asyncio.sleep(0.01)
        yield

    # After streaming finishes, if any leftover buffer, synthesize it too
    if buffer.strip():
        frag_text = buffer.strip()
        await ws.send_json({"type": "text_fragment", "fragment": frag_text})
        audio_bytes = synthesize_text_to_bytes(frag_text, voice_name=voice_name, speaking_rate=speaking_rate, audio_encoding=audio_encoding)
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        await ws.send_json({"type": "audio_chunk", "audio_b64": b64, "audio_encoding": audio_encoding})
    return
