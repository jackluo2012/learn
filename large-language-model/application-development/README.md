###  Xinference 使用这个平替 openai 接口
[xinference 官方文档 ](https://inference.readthedocs.io/zh-cn/latest/getting_started/using_xinference.html)
```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="not used actually")

response = client.chat.completions.create(
    model="my-llama-2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the largest animal?"}
    ]
)
print(response)
```
