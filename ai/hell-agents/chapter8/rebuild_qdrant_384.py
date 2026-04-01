#!/usr/bin/env python3
"""重建Qdrant集合为384维（匹配本地embedding模型）"""
import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=url, api_key=api_key)

# 需要重建的集合列表
collections_to_rebuild = [
    "hello_agents_vectors",
    "rag_knowledge_base"
]

print("🔧 重建Qdrant集合为384维...")
print("="*60)

for collection_name in collections_to_rebuild:
    print(f"\n📦 处理集合: {collection_name}")

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name in collection_names:
        info = client.get_collection(collection_name)
        current_dim = info.config.params.vectors.size
        points_count = info.points_count

        print(f"   当前维度: {current_dim}, 向量数: {points_count}")

        # 删除旧集合
        print(f"   🗑️  删除旧集合...")
        client.delete_collection(collection_name)
        print(f"   ✅ 已删除")
    else:
        print(f"   ℹ️  集合不存在，将创建")

    # 创建新集合（384维）
    print(f"   🔧 创建新集合（384维）...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print(f"   ✅ 创建成功")

print("\n" + "="*60)
print("✅ 所有集合已重建为384维！")
print("\n现在运行 Q&A Assistant:")
print("  python chapter8/11_Q&A_Assistant.py")
