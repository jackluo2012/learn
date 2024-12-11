import requests
headers = {
    'Content-Type': 'application/json',
}
r= requests.get('http://localhost:1337/v1/models', headers=headers)
# print(r.json()) 

data = {
    'model': 'gpt-3.5-turbo',
    'messages': [
        {
            'role': 'user',
            'content': 'Hello!'
        }
    ],
    'stream': True
}
r = requests.post('http://localhost:1337/v1/chat/completions', headers=headers, json=data,stream=True)
print(r.json())