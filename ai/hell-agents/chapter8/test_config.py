#!/usr/bin/env python3
"""测试LLM和Embedding配置"""
import os
from dotenv import load_dotenv
load_dotenv()

print("📋 配置检查")
print("="*60)

# 1. 检查环境变量
print("\n1️⃣ LLM配置:")
print(f"   模型: {os.getenv('LLM_MODEL_ID')}")
print(f"   Base URL: {os.getenv('LLM_BASE_URL')}")
api_key = os.getenv('LLM_API_KEY', '')
print(f"   API Key: {api_key[:20]}...{api_key[-10:]}")

print("\n2️⃣ Embedding配置:")
print(f"   类型: {os.getenv('EMBED_MODEL_TYPE')}")
print(f"   模型: {os.getenv('EMBED_MODEL_NAME')}")

print("\n3️⃣ Qdrant配置:")
print(f"   URL: {os.getenv('QDRANT_URL')}")
print(f"   向量维度: {os.getenv('QDRANT_VECTOR_SIZE')}")

# 2. 测试Embedding
print("\n" + "="*60)
print("🧪 测试Embedding模型...")
try:
    from hello_agents.memory.embedding import get_text_embedder
    embedder = get_text_embedder()
    test_vec = embedder.encode("测试文本")
    print(f"✅ Embedding工作正常")
    print(f"   维度: {len(test_vec)}")
except Exception as e:
    print(f"❌ Embedding测试失败: {e}")

# 3. 测试LLM
print("\n🧪 测试LLM模型...")
try:
    from hello_agents.core.llm import HelloAgentsLLM
    llm = HelloAgentsLLM()
    response = llm.invoke([{"role": "user", "content": "Hi"}])
    print(f"✅ LLM工作正常")
    print(f"   响应: {response[:100]}...")
except Exception as e:
    print(f"❌ LLM测试失败: {e}")

# 4. 测试Qdrant
print("\n🧪 测试Qdrant连接...")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    collections = client.get_collections().collections
    print(f"✅ Qdrant连接成功")
    print(f"   集合数量: {len(collections)}")

    for col in collections:
        if col.name in ["hello_agents_vectors", "rag_knowledge_base"]:
            info = client.get_collection(col.name)
            print(f"   📦 {col.name}: {info.config.params.vectors.size}维, {info.points_count}向量")
except Exception as e:
    print(f"❌ Qdrant测试失败: {e}")

print("\n" + "="*60)
print("✨ 所有测试完成！现在可以运行:")
print("  python chapter8/11_Q&A_Assistant.py")
