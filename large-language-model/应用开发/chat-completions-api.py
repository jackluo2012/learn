import os

from openai import OpenAI

# 初始化 OpenAI
client = OpenAI(
                api_key="Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                base_url="http://localhost:1337/v1"
            )
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好,我叫tt"},
        {"role": "user", "content": "你好,tt"},
        {"role": "user", "content": "我叫什么名字"},
    ],
)
print(response)