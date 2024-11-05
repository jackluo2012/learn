from openai import OpenAI


client = OpenAI(
                api_key="Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                base_url="http://localhost:1337/v1"
            )
r = client.embeddings.create(
    model="text-embedding-ada-002",
    input=["Hello world!", "Hello again!"],
)
print(r)