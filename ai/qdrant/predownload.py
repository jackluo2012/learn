"""预下载 fastembed 所需模型到 local_cache（直连 huggingface.co + Xet 高速下载）"""
import os

# 不设 HF_ENDPOINT，直连官方（本机实测可直连，hf-mirror 反而重定向回官方且丢元数据头）
os.environ.pop("HF_ENDPOINT", None)
os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"  # Xet 多线程分块下载

from huggingface_hub import snapshot_download

BASE = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "preprocessor_config.json",
]

JOBS = [
    ("Qdrant/bge-small-zh-v1.5", BASE + ["model_optimized.onnx"]),   # fastembed 转换的 onnx 仓库
    ("BAAI/bge-reranker-base", BASE + ["onnx/model.onnx"]),
]

for repo, patterns in JOBS:
    print(f"=== 下载 {repo}: {patterns}", flush=True)
    path = snapshot_download(
        repo_id=repo,
        allow_patterns=patterns,
        cache_dir="/Users/jackluo/Data/learn/ai/qdrant/local_cache",
    )
    print(f"=== 完成 {repo} -> {path}", flush=True)
