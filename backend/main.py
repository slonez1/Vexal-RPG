from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
import openai
import logging

logging.basicConfig(level=logging.DEBUG)
# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to "*" for testing; refine for production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# Firestore initialization
db = firestore.Client()
GAME_STATE_DOC = "sessions/rpg_game_state"

# Logging setup for debugging
logging.basicConfig(level=logging.DEBUG)

# Pydantic models
class CommandInput(BaseModel):
    prompt: str

# --- Define Endpoints Below ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Vexal RPG Backend!"}

@app.post("/api/gm")
async def get_gpt_response(command: CommandInput):
    try:
        # Load the game state
        logging.info(f"Player command received: {command.prompt}")
        game_state_doc = db.document(GAME_STATE_DOC).get()
        game_state = game_state_doc.to_dict() if game_state_doc.exists else {}

        # Sample GPT-4 AI response based on testing context
        state_summary = f"""
        Testing Context:
        Player Stats: Health={game_state.get('player', {}).get('hp', '100')} Mana={game_state.get('player', {}).get('mana', '30')}
        Attributes: {game_state.get('player', {}).get('attributes', {})}
        """
        prompt_for_test = f"This is a test session. Respond as if you are debugging an AI GM logic."

        # Call GPT for a testing-specific response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI Game Master in a testing mode. Optimize responses for debugging."},
                {"role": "assistant", "content": state_summary},
                {"role": "user", "content": command.prompt},
            ],
            max_tokens=500,
            temperature=0.5,
        )

        # Process and log the GM response
        gm_response = response["choices"][0]["message"]["content"].strip()
        logging.info(f"GM test response: {gm_response}")

        # Return the GM response
        return {"response": gm_response}
    except Exception as e:
        logging.error(f"Error processing command: {e}")
        return {"error": str(e)}