import os, glob
for f in glob.glob('**/*.py', recursive=True):
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for lineno, line in enumerate(fp, 1):
                if 'OPENAI_API_KEY' in line or 'from openai' in line or 'import openai' in line:
                    print(f'{f}:{lineno}: {line.rstrip()}')
    except Exception as e:
        print(f'Error reading {f}: {e}')