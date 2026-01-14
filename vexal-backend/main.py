from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
import openai
import logging
import os

# === ENVIRONMENT CONFIGURATION ===
logging.basicConfig(level=logging.DEBUG)

# === Load OpenAI API Key ===
OPENAI_API_KEY = None

# OPTION 1: OpenAI API key as ENV VAR
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logging.debug(f"Using OpenAI API key: {OPENAI_API_KEY[:8]}... (truncated)")
else:
    # OPTION 2: OpenAI API key from Secret File
    OPENAI_KEY_PATH = "/secrets/openai_api_key"
    try:
        with open(OPENAI_KEY_PATH, "r") as key_file:
            OPENAI_API_KEY = key_file.read().strip()
            logging.debug(f"Using OpenAI API key from secret file at {OPENAI_KEY_PATH}.")
    except FileNotFoundError:
        logging.error(f"OpenAI API key is missing. Check the environment configuration for Cloud Run.")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    logging.error("Critical: OpenAI API key could not be loaded, functionality will be limited.")

# === FASTAPI INITIALIZATION ===
app = FastAPI()

# Enable CORS: Allow client requests from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Set up Firestore Database Connection ===
try:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/secrets/service_account.json")
    if os.path.exists(credentials_path):  # Ensure credentials file exists
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        db = firestore.Client()
        GAME_STATE_DOC = "sessions/rpg_game_state"
        logging.info("Successfully connected to Firestore.")
    else:
        logging.error(f"Firestore credentials file not found at {credentials_path}")
        db = None
except Exception as firestore_error:
    logging.error(f"Error initializing Firestore: {firestore_error}")
    db = None


# === PYDANTIC DATA MODELS ===
class CommandInput(BaseModel):
    prompt: str


# === UTILITY FUNCTIONS ===

def update_game_state(game_state, gm_response):
    """
    Updates the game state based on the GM response or player actions.
    """
    logging.info("Updating game state...")

    # Parse GM response for predefined actions
    response_lower = gm_response.lower()

    if "you are attacked" in response_lower:
        logging.info("Player attacked: reduce HP by 10")
        game_state["player"]["hp"] -= 10

    elif "you cast" in response_lower:
        logging.info("Player casts spell: reduce Mana by 5")
        game_state["player"]["mana"] -= 5

    elif "you attack" in response_lower:
        logging.info("Player attacks: reduce Stamina by 5")
        game_state["player"]["stamina"] -= 5

    # Ensure no attributes go below zero
    for key in ["hp", "mana", "stamina"]:
        game_state["player"][key] = max(0, game_state["player"].get(key, 0))

    logging.info(f"Updated game state: {game_state}")
    return game_state


def save_game_state(game_state):
    """
    Saves the updated game state to Firestore.
    """
    try:
        if db is None:
            logging.warning("Database connection is unavailable. Cannot save game state.")
            return

        db.document(GAME_STATE_DOC).set(game_state)
        logging.info("Game state successfully saved to Firestore.")
    except Exception as save_error:
        logging.error(f"Error saving game state to Firestore: {save_error}")


# === API ROUTES ===

@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    """
    Processes user commands, interacts with OpenAI API, and updates game state.
    """
    if not db:
        logging.error("Firestore database connection is unavailable.")
        return {"error": "Could not connect to Firestore. Please contact the administrator."}, 500

    try:
        # Validate the input
        if not command.prompt.strip():
            logging.warning("Received an empty or invalid prompt.")
            return {"error": "Command input cannot be empty."}, 400

        # Retrieve the current game state
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Default game state if none exists
        game_state.setdefault("player", {
            "hp": 100,
            "mana": 50,
            "stamina": 30,
        })

        # Summarize the current game state for the AI
        state_summary = f"""
        RPG GAME STATE:
        Player Stats:
        - HP: {game_state['player']['hp']}
        - Mana: {game_state['player']['mana']}
        - Stamina: {game_state['player']['stamina']}
        """

        # Call OpenAI to get the GM's response
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use GPT-4 or other compatible model
            messages=[
                {"role": "system", "content": "You are an RPG Game Master. Simulate a game scenario."},
                {"role": "assistant", "content": state_summary.strip()},
                {"role": "user", "content": command.prompt.strip()},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        gm_response = response["choices"][0]["message"]["content"].strip()
        logging.info(f"GM Response: {gm_response}")

        # Update and save the game state
        game_state = update_game_state(game_state, gm_response)
        save_game_state(game_state)

        # Return the response and updated game state to the user
        return {"response": gm_response, "game_state": game_state}

    except Exception as critical_error:
        logging.error(f"Critical error: {critical_error}")
        return {"error": "An unexpected error occurred. Please try again later."}, 500
