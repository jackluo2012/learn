import os 
from openai import OpenAI

# 初始化 OpenAI
client = OpenAI(
                api_key="Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                base_url="http://localhost:1337/v1"
            )
#print(chat_completion.choices[0].message.content)
# 与大模型交互函数
def chat(prompt,model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content

answer = chat('美国的总统是谁？')
print(answer)
answer = chat('小明中奖了，他要去')
print(answer)