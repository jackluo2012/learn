# Search for where OpenAICompletion is instantiated in crewai package
import os, glob

crewai_path = ".venv/lib/python3.12/site-packages/crewai"
for f in glob.glob(f"{crewai_path}/**/*.py", recursive=True):
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for lineno, line in enumerate(fp, 1):
                if 'OpenAICompletion(' in line or 'AnthropicCompletion(' in line:
                    print(f'{f}:{lineno}: {line.rstrip()}')
    except Exception:
        pass