import openai

# Assume that the model is already launched.
# The api_key can't be empty, any string is OK.
client = openai.Client(api_key="not empty", base_url="http://localhost:9997/v1")
client.chat.completions.create(
    model='qwen2.5-instruct',
    messages=[
        {
            "content": "What is the largest animal?",
            "role": "user",
        }
    ],
    max_tokens=1024
)