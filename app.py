from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from game_state import (
    init_session_state,
    advance_game_time,
    update_condition_timers,
    format_game_datetime,
    get_gs_copy,
    get_effective_stats,
)
from gm_ai import get_gm_response, trigger_tts

# Initialize FastAPI app
app = FastAPI()

# Static files and templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Session state initialization
session_state = {}
init_session_state(session_state)

# --- ROUTES --- #

@app.get("/", response_class=HTMLResponse)
async def gm_tts_page(request: Request):
    """
    GM TTS Page (currently hosted on the working / page).
    """
    return templates.TemplateResponse(
        "tts.html",
        {
            "request": request,
            "header": "GM Stream + TTS",
            "voice": "en-US-Wavenet-D",
            "target_words": 800,
            "recent_n": 5,
        },
    )

@app.get("/ui", response_class=HTMLResponse)
async def core_ui_page(request: Request):
    """
    Core UI Page (centralized game console).
    Incorporates elements like in-game time, stats, and updates.
    """
    game_time = format_game_datetime(session_state)
    effective_stats = get_effective_stats(session_state)

    # Render the recreated Streamlit components in a modular fashion
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "game_time": game_time,
            "stats": effective_stats["attributes"],
        },
    )


@app.post("/advance_time", response_class=HTMLResponse)
async def advance_time(request: Request, turns: int = Form(...)):
    """
    Advance the game time, update state, and refresh the page data.
    """
    new_time = advance_game_time(session_state, turns)
    game_time = format_game_datetime(session_state)
    return {"success": True, "new_time": new_time}


@app.post("/get_gm_response", response_class=HTMLResponse)
async def gm_response(request: Request, input_text: str = Form(...)):
    """
    Fetch GM AI response (keeping logic from gm_ai).
    """
    response = get_gm_response(input_text)
    return {"success": True, "response": response}
