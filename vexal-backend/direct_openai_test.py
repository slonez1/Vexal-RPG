import openai

# Replace with your actual API key
openai.api_key = "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"

models_to_test = ["gpt-4", "gpt-4-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-0613"]
print("Testing available models with your API key...")

for model in models_to_test:
    try:
        print(f"Testing {model}...")
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, which model am I speaking to?"}],
            max_tokens=50,
        )
        print(f"{model} responded:")
        print(response["choices"][0]["message"]["content"])
    except openai.error.AuthenticationError:
        print(f"Error: Invalid API key or insufficient permissions for {model}.")
    except openai.error.OpenAIError as e:
        print(f"Error: {model} failed with error: {e}")