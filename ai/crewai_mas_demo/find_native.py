import os, glob

# Search in venv crewai package
crewai_path = ".venv/lib/python3.12/site-packages/crewai"
for f in glob.glob(f"{crewai_path}/**/*.py", recursive=True):
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for lineno, line in enumerate(fp, 1):
                if 'native provider' in line.lower() or 'OPENAI_API_KEY' in line:
                    print(f'{f}:{lineno}: {line.rstrip()}')
    except Exception as e:
        pass