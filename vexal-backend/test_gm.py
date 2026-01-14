import openai

# Example Game State for Context
game_state_summary = """
You are a player with the following stats:
HP: 100, Mana: 80, Stamina: 50
Conditions: Frightened, Blessed
Attributes: STR: 16, DEX: 14, CON: 15, WIS: 12, CHA: 10
In your hands, you hold a steel longsword.
"""

# Example Player Action
player_action = "attack myself"

# OpenAI GPT Call
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an immersive RPG AI GM. Use state knowledge to guide the story and apply rules."},
        {"role": "assistant", "content": game_state_summary},
        {"role": "user", "content": player_action},
    ],
    max_tokens=100,
    temperature=0.7,
)

# Print GM Response
print("GM Response:", response["choices"][0]["message"]["content"])