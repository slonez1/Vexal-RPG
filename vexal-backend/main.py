from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
import openai
import logging
import os
from dotenv import load_dotenv

# === ENVIRONMENT CONFIGURATION ===
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-5.2"  # Set GPT-5.2 as the default model
logging.basicConfig(level=logging.DEBUG)

if OPENAI_API_KEY:
    logging.debug(f"Using OpenAI API key: {OPENAI_API_KEY[:8]}... (truncated)")
    openai.api_key = OPENAI_API_KEY
else:
    logging.error("OpenAI API key is missing. Please check your `.env` file or environment variables.")

# === FASTAPI INITIALIZATION ===
app = FastAPI()

# Cross-Origin Resource Sharing (CORS): Allow client-side requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === FIRESTORE DATABASE CONNECTION ===
try:
    db = firestore.Client()
    GAME_STATE_DOC = "sessions/rpg_game_state"  # Define your Firestore document path
    logging.info("Successfully connected to Firestore.")
except Exception as firestore_error:
    db = None
    logging.error(f"Error connecting to Firestore: {firestore_error}")

# === PYDANTIC DATA MODELS ===
class CommandInput(BaseModel):
    prompt: str  # Define an input schema for player commands


# === UTILITY FUNCTIONS ===

def update_game_state(game_state, gm_response):
    """
    Updates the game state based on the GM response or player actions.
    """
    logging.info("Updating game state...")

    # Parse GM response for predefined actions
    response_lower = gm_response.lower()

    if "you are attacked" in response_lower:
        # Simulated attack case: reduce HP by 10
        logging.info("Player is attacked: reducing HP by 10")
        game_state["player"]["hp"] -= 10

    elif "you cast" in response_lower:
        # Simulated spell cast: reduce mana by 5
        logging.info("Player casts a spell: reducing Mana by 5")
        game_state["player"]["mana"] -= 5

    elif "you attack" in response_lower:
        # Simulated attack: reduce stamina by 5
        logging.info("Player attacks: reducing Stamina by 5")
        game_state["player"]["stamina"] -= 5

    # Ensure no stats go below zero
    game_state["player"]["hp"] = max(game_state["player"]["hp"], 0)
    game_state["player"]["mana"] = max(game_state["player"]["mana"], 0)
    game_state["player"]["stamina"] = max(game_state["player"]["stamina"], 0)

    logging.info(f"Updated game state: {game_state}")
    return game_state


def save_game_state(game_state):
    """
    Saves the updated game state back to Firestore.
    """
    try:
        if not db:
            logging.warning("Database connection unavailable: unable to update game state.")
            return

        db.document(GAME_STATE_DOC).set(game_state)
        logging.info("Game state successfully saved to Firestore.")
    except Exception as e:
        logging.error(f"Error saving game state to Firestore: {e}")


# === API ROUTES ===

@app.get("/")
async def root():
    """
    Serves as the root endpoint.
    """
    return {"message": "Welcome to the FastAPI RPG Game Master API! Send requests to /api/gm."}


@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    """
    Uses OpenAI to generate GM responses and updates the player's game state based on actions.
    """
    if not db:
        logging.error("Firestore database error. Cannot process any player commands.")
        return {"error": "Database connection to Firestore is missing. Please contact the administrator."}, 500

    try:
        # Validate the player's input command
        if not command.prompt.strip():
            logging.warning("Player provided an invalid or empty command.")
            return {"error": "Command input cannot be empty."}, 400

        # Load the current game state
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Summarize the game state for the Test GM scenario
        state_summary = f"""
        TEST GM SCENARIO
        **Player Stats**
        - HP: {game_state.get('player', {}).get('hp', 100)}
        - Mana: {game_state.get('player', {}).get('mana', 50)}
        - Stamina: {game_state.get('player', {}).get('stamina', 30)}
        """

        # Generate a GM response using OpenAI API
        response = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,  # Select GPT model
            messages=[
                {"role": "system", "content": "You are an AI RPG Game Master. Simulate a Test GM scenario."},
                {"role": "assistant", "content": f"{state_summary.strip()}"},
                {"role": "user", "content": command.prompt.strip()},
            ],
            max_completion_tokens=500,
            temperature=0.7,
        )

        gm_response = response["choices"][0]["message"]["content"].strip()
        logging.info(f"GM Response: {gm_response}")

        # Update game state based on GM response
        game_state = update_game_state(game_state, gm_response)

        # Save the updated game state to Firestore
        save_game_state(game_state)

        # Return the GM response and the updated game state to the client
        return {"response": gm_response, "game_state": game_state}

    except Exception as error:
        logging.error(f"An unexpected server error occurred: {error}")
        return {"error": "An error occurred while processing your command. Please try again later."}, 500
