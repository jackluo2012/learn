#!/usr/bin/env python3
"""检查所有Qdrant集合"""
import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient

url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=url, api_key=api_key)

print("🔍 Qdrant云服务中的所有集合:")
print("="*60)

collections = client.get_collections().collections

if not collections:
    print("⚠️ 没有找到任何集合")
else:
    for col in collections:
        print(f"\n📦 集合名称: {col.name}")
        try:
            info = client.get_collection(col.name)
            vectors = info.config.params.vectors
            if hasattr(vectors, 'size'):
                print(f"   向量维度: {vectors.size}")
                print(f"   距离度量: {vectors.distance}")
            print(f"   向量数量: {info.points_count}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

print("\n" + "="*60)
