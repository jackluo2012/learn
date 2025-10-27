from xmindparser import xmind_to_dict
import pandas as pd
import os

def flatten_xmind(topics, parent_chain=None):
    rows = []
    for t in topics:
        name = t.get('title', '')
        chain = parent_chain + [name] if parent_chain else [name]
        rows.append(chain)
        if 'topics' in t:
            rows.extend(flatten_xmind(t['topics'], chain))
    return rows

def convert_xmind_to_excel(file_path):
    data = xmind_to_dict(file_path)[0]['topic']
    rows = flatten_xmind([data])
    max_depth = max(len(r) for r in rows)
    for r in rows:
        r.extend([""] * (max_depth - len(r)))

    df = pd.DataFrame(rows, columns=[f"Level {i+1}" for i in range(max_depth)])
    output_path = os.path.splitext(file_path)[0] + ".xlsx"
    df.to_excel(output_path, index=False)
    print(f"✅ 已生成: {output_path}")

if __name__ == "__main__":
    file_name = input("请输入要转换的 .xmind 文件路径: ").strip('"')
    convert_xmind_to_excel(file_name)
