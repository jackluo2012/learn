#!/usr/bin/env python3
"""完整测试 Q&A Assistant 流程"""
import os
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("🧪 完整流程测试")
print("="*60)

# 1. 测试导入
print("\n[1/5] 测试导入...")
try:
    import sys
    sys.path.insert(0, '/home/jackluo/my/learn/ai/hell-agents')
    from chapter8.Eleven_QA_Assistant import PDFLearningAssistant
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    # 尝试直接导入
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("qa_module", "/home/jackluo/my/learn/ai/hell-agents/chapter8/11_Q&A_Assistant.py")
        qa_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qa_module)
        PDFLearningAssistant = qa_module.PDFLearningAssistant
        print("✅ 导入成功（备用方法）")
    except Exception as e2:
        print(f"❌ 导入完全失败: {e2}")
        exit(1)

# 2. 测试初始化
print("\n[2/4] 测试初始化...")
try:
    assistant = PDFLearningAssistant(user_id="test_user")
    print("✅ 初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    exit(1)

# 3. 测试添加笔记（不需要PDF）
print("\n[3/4] 测试添加笔记...")
try:
    assistant.add_note("测试笔记：这是一个测试", concept="测试")
    print("✅ 添加笔记成功")
except Exception as e:
    print(f"❌ 添加笔记失败: {e}")
    exit(1)

# 4. 测试回顾（不需要PDF）
print("\n[4/4] 测试回顾...")
try:
    result = assistant.recall("测试", limit=3)
    print(f"✅ 回顾成功")
    print(f"结果: {result[:100]}...")
except Exception as e:
    print(f"❌ 回顾失败: {e}")
    exit(1)

# 5. 测试统计
print("\n[5/5] 测试统计...")
try:
    stats = assistant.get_stats()
    print("✅ 统计成功")
    for key, value in stats.items():
        print(f"  {key}: {value}")
except Exception as e:
    print(f"❌ 统计失败: {e}")

print("\n" + "="*60)
print("✨ 基础功能测试完成！")
print("="*60)
print("\n注意：PDF加载和问答功能需要在Web界面中测试")
