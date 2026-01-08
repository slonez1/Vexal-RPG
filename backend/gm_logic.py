from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware for UI compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firestore configuration
db = firestore.Client()
GAME_STATE_DOC = "sessions/rpg_game_state"


# Pydantic Models
class CommandInput(BaseModel):
    prompt: str


# Fetch Game State
@app.get("/api/state")
async def fetch_game_state():
    """
    Fetch the entire current game state from Firestore to sync with the frontend.
    """
    try:
        game_state_doc = db.document(GAME_STATE_DOC).get()
        if not game_state_doc.exists:
            return {"error": "Game state not found."}
        return game_state_doc.to_dict()
    except Exception as e:
        logging.error(f"[Fetch State Error] {e}")
        return {"error": str(e)}


# Process Player Commands
@app.post("/api/gm")
async def process_command(command: CommandInput):
    """
    Process player commands, update state, and return GM response.
    """
    try:
        game_state = db.document(GAME_STATE_DOC).get().to_dict() or {}
        player = game_state.setdefault("player", {
            "hp": 100,
            "hp_max": 100,
            "mana": 50,
            "mana_max": 50,
            "stamina": 50,
            "stamina_max": 50,
            "xp": 0,
            "level": 1,
            "skills": {"Attack": 1},
            "conditions": {}
        })

        logging.info(f"[GM Command Received] {command.prompt}")
        response_message = "Nothing happened."  # Default GM response

        # Example: Combat Command
        if "goblin attacks" in command.prompt.lower():
            damage = 15
            player["hp"] = max(0, player["hp"] - damage)
            if "Wounded" not in player["conditions"]:
                player["conditions"]["Wounded"] = {"timer": 3}
            response_message = f"The goblin hit you for {damage} damage! HP: {player['hp']}/{player['hp_max']}."

        # Example: Cast Spell
        elif "cast spell" in command.prompt.lower():
            mana_cost = 10
            if player["mana"] >= mana_cost:
                player["mana"] -= mana_cost
                player["conditions"]["Blessed"] = {"timer": 3}
                response_message = f"You cast a spell! Mana: {player['mana']}/{player['mana_max']}."
            else:
                response_message = "You don't have enough Mana!"

        # Example: Gain XP / Level Up
        elif "gain xp" in command.prompt.lower():
            gained_xp = 50
            player["xp"] += gained_xp
            if player["xp"] >= 100:  # Level up
                player["xp"] -= 100
                player["level"] += 1
                player["hp_max"] += 10
                player["mana_max"] += 5
                player["stamina_max"] += 5
                response_message = f"Level Up! You are now Level {player['level']}."
            else:
                response_message = f"You gained {gained_xp} XP! Current XP: {player['xp']}/100."

        # Manage Condition Timers
        for condition, details in list(player["conditions"].items()):
            timer = details.get("timer", 0)
            if timer > 1:
                player["conditions"][condition]["timer"] -= 1
            else:
                del player["conditions"][condition]  # Remove expired condition

        # Save the updated state back into Firestore
        db.document(GAME_STATE_DOC).set(game_state)
        logging.info(f"[Game State Updated] {game_state}")

        return {"response": response_message}

    except Exception as e:
        logging.error(f"[Command Processing Error] {e}")
        return {"error": str(e)}