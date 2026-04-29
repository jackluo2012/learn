import re

with open('.venv/lib/python3.12/site-packages/crewai/llm.py', 'r') as f:
    content = f.read()

# Find SUPPORTED_NATIVE_PROVIDERS
idx = content.find('SUPPORTED_NATIVE_PROVIDERS')
if idx >= 0:
    print(content[idx:idx+500])

# Find OPENAI_MODELS
idx = content.find('OPENAI_MODELS')
if idx >= 0:
    print(content[idx:idx+300])