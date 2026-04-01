#!/usr/bin/env python3
"""检查并刷新embedding维度"""
import os
from dotenv import load_dotenv
load_dotenv()

from hello_agents.memory.embedding import get_text_embedder, get_dimension, refresh_embedder

print("📊 当前embedding配置:")
print(f"EMBED_MODEL_TYPE: {os.getenv('EMBED_MODEL_TYPE')}")
print(f"EMBED_MODEL_NAME: {os.getenv('EMBED_MODEL_NAME')}")
print(f"EMBED_BASE_URL: {os.getenv('EMBED_BASE_URL')}")
print(f"EMBED_API_KEY: {os.getenv('EMBED_API_KEY', '***')[:20]}...")

print("\n🔍 检查旧embedder维度（缓存）:")
try:
    old_embedder = get_text_embedder()
    old_dim = old_embedder.dimension
    print(f"旧维度: {old_dim}")
except Exception as e:
    print(f"获取失败: {e}")
    old_dim = None

print("\n🔄 刷新embedder...")
try:
    new_embedder = refresh_embedder()
    new_dim = new_embedder.dimension
    print(f"✅ 新维度: {new_dim}")

    # 测试编码
    test_vec = new_embedder.encode("测试文本")
    print(f"✅ 测试向量形状: {test_vec.shape if hasattr(test_vec, 'shape') else len(test_vec)}")

except Exception as e:
    print(f"❌ 刷新失败: {e}")

print("\n✨ 现在可以运行 Q&A Assistant 了")
