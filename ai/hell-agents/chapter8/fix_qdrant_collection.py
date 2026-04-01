#!/usr/bin/env python3
"""删除旧的Qdrant集合并重建"""
import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# 连接配置
url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=url, api_key=api_key)
collection_name = "rag_knowledge_base"

print(f"连接到Qdrant: {url}")
print(f"集合名称: {collection_name}")

# 检查集合是否存在
collections = client.get_collections().collections
collection_names = [c.name for c in collections]

if collection_name in collection_names:
    print(f"✅ 找到集合 '{collection_name}'")

    # 获取集合信息
    info = client.get_collection(collection_name)
    print(f"📊 当前向量维度: {info.config.params.vectors.size}")
    print(f"📊 当前向量数量: {info.points_count}")

    # 确认删除
    confirm = input(f"\n确定要删除集合 '{collection_name}' 吗？(yes/no): ")
    if confirm.lower() in ["yes", "y"]:
        client.delete_collection(collection_name)
        print(f"✅ 集合已删除")
    else:
        print("❌ 取消删除")
        exit(0)
else:
    print(f"ℹ️  集合 '{collection_name}' 不存在，将自动创建")

# 创建新集合（2048维，用于doubao-embedding-vision-251215）
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
