from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
import openai
import logging
import os
from dotenv import load_dotenv
#from openai import AuthenticationError, RateLimitError, OpenAIError

# === ENVIRONMENT CONFIGURATION ===
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logging.basicConfig(level=logging.DEBUG)  # Ensure all logs are visible (DEBUG level)

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


# === ROUTES AND FUNCTIONALITY ===

@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    """
    Uses OpenAI GPT to generate role-playing responses based on player actions.
    """
    if not db:
        logging.error("Firestore database error. Cannot process any player commands.")
        return {"error": "Firestore database is not working. Please contact the administrator."}, 500

    try:
        # Validate the player's input command
        if not command.prompt.strip():
            logging.warning("Received an invalid or empty player command.")
            return {"error": "Command input cannot be empty."}, 400

        # Load the current game state
        logging.info("Retrieving the current game state for the player...")
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Summarize the game state for context in GPT prompts
        state_summary = f"""
        Player Stats:
        Location: {game_state.get('player', {}).get('location', 'unknown')},
        HP: {game_state.get('player', {}).get('hp', 100)}/{game_state.get('player', {}).get('hp_max', 100)},
        Mana: {game_state.get('player', {}).get('mana', 50)}/{game_state.get('player', {}).get('mana_max', 50)},
        Stamina: {game_state.get('player', {}).get('stamina', 30)}/{game_state.get('player', {}).get('stamina_max', 30)}
        """
        logging.info("Game state context prepared.")

        # Generate a response using a supported OpenAI model
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Replace with "gpt-4" if that's available for you
            messages=[
                {"role": "system", "content": "You are an AI-driven RPG Game Master, helping players navigate the world."},
                {"role": "assistant", "content": state_summary.strip()},
                {"role": "user", "content": command.prompt.strip()},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        gpt_response = response["choices"][0]["message"]["content"].strip()
        logging.info(f"Player response from GPT: {gpt_response}")
        return {"response": gpt_response}

    except Exception as error:
        logging.error(f"An unexpected server error occurred: {error}")
        return {"error": "An error occurred while processing your command. Please try again later."}, 500


@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    if not db:
        logging.error("Firestore database error. Cannot process any player commands.")
        return {"error": "Firestore database is not working. Please contact the administrator."}, 500

    try:
        # Check for valid command prompt
        if not command.prompt.strip():
            logging.warning("Received an invalid or empty player command.")
            return {"error": "Command input cannot be empty."}, 400

        # Retrieve game state
        logging.info("Retrieving current game state for the player...")
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Prepare GPT request with player stats
        state_summary = f"""
            Player Stats:
            Location: {game_state.get('player', {}).get('location', 'unknown')},
            HP: {game_state.get('player', {}).get('hp', 100)}/{game_state.get('player', {}).get('hp_max', 100)},
            Mana: {game_state.get('player', {}).get('mana', 50)}/{game_state.get('player', {}).get('mana_max', 50)},
            Stamina: {game_state.get('player', {}).get('stamina', 30)}/{game_state.get('player', {}).get('stamina_max', 30)}
        """
        logging.info("Game state context prepared.")

        # Generate OpenAI API response
        response = openai.Completion.create(
            engine="text-davinci-003", 
            prompt=f"{state_summary}\n\nPlayer Command: {command.prompt.strip()}",
            max_tokens=500,
            temperature=0.7,
        )

        gpt_response = response.choices[0].text.strip()
        logging.info(f"Player response from GPT: {gpt_response}")
        return {"response": gpt_response}

    except Exception as error:
        logging.error(f"Error fetching GPT response: {error}")
        return {"error": "An error occurred while processing your command. Please try again later."}, 500

    except AuthenticationError:
        logging.error("Authentication error: OpenAI API Key is invalid!")
        return {"error": "Authentication error: Invalid API key provided. Please check your setup."}, 401

    except RateLimitError:
        logging.error("Rate limit exceeded for OpenAI API usage!")
        return {"error": "Rate limit exceeded. Please slow down your requests and retry later."}, 429

    except OpenAIError as error:
        logging.error(f"OpenAI API encountered an error: {error}")
        return {"error": "OpenAI API encountered an internal error."}, 500

    except Exception as error:
        logging.error(f"An unexpected server error occurred: {error}")
        return {"error": f"Unexpected server error: {error}"}, 500
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
logging.basicConfig(level=logging.DEBUG)  # Ensure all logs are visible (DEBUG level)

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


# === ROUTES AND FUNCTIONALITY ===
@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    """
    Uses OpenAI GPT to generate role-playing responses based on player actions.
    """
    if not db:
        logging.error("Firestore database error. Cannot process any player commands.")
        return {"error": "Firestore database is not working. Please contact the administrator."}, 500

    try:
        # Validate the player's input command
        if not command.prompt.strip():
            logging.warning("Received an invalid or empty player command.")
            return {"error": "Command input cannot be empty."}, 400

        # Load the current game state
        logging.info("Retrieving the current game state for the player...")
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Summarize the game state for context in GPT prompts
        state_summary = f"""
        Player Stats:
        Location: {game_state.get('player', {}).get('location', 'unknown')},
        HP: {game_state.get('player', {}).get('hp', 100)}/{game_state.get('player', {}).get('hp_max', 100)},
        Mana: {game_state.get('player', {}).get('mana', 50)}/{game_state.get('player', {}).get('mana_max', 50)},
        Stamina: {game_state.get('player', {}).get('stamina', 30)}/{game_state.get('player', {}).get('stamina_max', 30)}
        """
        logging.info("Game state context prepared.")

        # Select Model and API Call
        if os.getenv("OPENAI_MODEL_VERSION", "0.28") == "0.28":
            # OpenAI API for 0.28 compatibility
            logging.debug("Using OpenAI API version 0.28...")
            response = openai.Completion.create(
                engine="text-davinci-003", 
                prompt=f"{state_summary}\n\nPlayer Command: {command.prompt.strip()}",
                max_tokens=500,
                temperature=0.7,
            )
            gpt_response = response["choices"][0]["text"].strip()
        else:
            # OpenAI API for >=1.0 compatibility
            logging.debug("Using OpenAI API version >=1.0...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Replace with "gpt-4" if available and preferred
                messages=[
                    {"role": "system", "content": "You are an AI-driven RPG Game Master, helping players navigate the world."},
                    {"role": "assistant", "content": state_summary.strip()},
                    {"role": "user", "content": command.prompt.strip()},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            gpt_response = response["choices"][0]["message"]["content"].strip()

        logging.info(f"Player response from GPT: {gpt_response}")
        return {"response": gpt_response}

    except Exception as error:
        logging.error(f"An unexpected server error occurred: {error}")
        return {"error": "An error occurred while processing your command. Please try again later."}, 500