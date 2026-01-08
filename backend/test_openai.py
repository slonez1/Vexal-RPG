import openai

openai.api_key = "your-api-key-here"

print(f"OpenAI Version: {openai.__version__}")

try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Describe a vibrant forest."},
        ],
        max_tokens=100,
        temperature=0.7,
    )
    print("Response:", response["choices"][0]["message"]["content"])
except Exception as e:
    print("Error:", e)