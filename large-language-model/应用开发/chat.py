import os
import openai

client = openai.OpenAI(
                api_key="Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                base_url="http://localhost:1337/v1"
            )

chat_history = []
while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break
    chat_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_history,
    )
    print("GPT: ", response.choices[0].message.content)