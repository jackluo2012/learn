#!/usr/bin/env python3
"""快速测试核心功能"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("🧪 快速测试")
print("="*60)

# 添加路径
sys.path.insert(0, '/home/jackluo/my/learn/ai/hell-agents')

# 测试导入
print("\n[1/3] 测试工具导入...")
try:
    from hello_agents.tools import MemoryTool, RAGTool
    print("✅ 工具导入成功")
except Exception as e:
    print(f"❌ 工具导入失败: {e}")
    exit(1)

# 测试MemoryTool
print("\n[2/3] 测试 MemoryTool...")
try:
    memory = MemoryTool(user_id="quick_test")
    result = memory.execute("add", content="测试记忆", memory_type="semantic", importance=0.5)
    print(f"✅ MemoryTool 工作正常")
    print(f"   结果: {result[:50]}...")
except Exception as e:
    print(f"❌ MemoryTool 失败: {e}")

# 测试RAGTool
print("\n[3/3] 测试 RAGTool...")
try:
    rag = RAGTool(rag_namespace="quick_test")
    # 添加文本
    result = rag.execute("add_text", text="这是测试文本。Python是一种编程语言。", chunk_size=50, chunk_overlap=10)
    print(f"✅ RAGTool 添加文本成功")
    print(f"   结果: {result[:100]}...")

    # 测试搜索
    search_result = rag.execute("search", query="Python", limit=2)
    print(f"✅ RAGTool 搜索成功")
    print(f"   结果: {search_result[:100]}...")

except Exception as e:
    print(f"❌ RAGTool 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✨ 测试完成")
print("="*60)
