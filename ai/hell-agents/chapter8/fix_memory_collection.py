#!/usr/bin/env python3
"""删除并重建MemoryTool使用的Qdrant集合"""
import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=url, api_key=api_key)

# MemoryTool使用的集合名称
collection_name = "hello_agents_vectors"

print(f"🔍 检查集合: {collection_name}")

collections = client.get_collections().collections
collection_names = [c.name for c in collections]

if collection_name in collection_names:
    info = client.get_collection(collection_name)
    print(f"📊 当前维度: {info.config.params.vectors.size}")
    print(f"📊 向量数量: {info.points_count}")

    # 删除旧集合
    print(f"\n🗑️  删除集合 {collection_name}...")
    client.delete_collection(collection_name)
    print(f"✅ 已删除")
else:
    print(f"ℹ️  集合不存在")

# 创建新集合（2048维）
print(f"\n🔧 创建新集合（2048维）...")
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=2048, distance=Distance.COSINE)
)

# 验证
new_info = client.get_collection(collection_name)
print(f"✅ 新集合创建成功！")
print(f"📊 向量维度: {new_info.config.params.vectors.size}")
print(f"📊 距离度量: {new_info.config.params.vectors.distance}")

print(f"\n✨ 现在可以运行 Q&A Assistant 了！")
