import openai

try:
    # Confirm OpenAI is properly loaded
    api_key = "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"
    openai.api_key = api_key
    
    # Test a GPT-4 chat completion
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello, test OpenAI GPT-4"}],
        max_tokens=50
    )
    print("Success! GPT-4 responded:")
    print(response["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error: {e}")