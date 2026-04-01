#!/usr/bin/env python3
"""端到端测试：PDF加载 + 问答"""
import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, '/home/jackluo/my/learn/ai/hell-agents')

print("="*60)
print("🧪 端到端测试：PDF加载 + 智能问答")
print("="*60)

# 导入模块
print("\n[1/6] 导入模块...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "qa_module",
        "/home/jackluo/my/learn/ai/hell-agents/chapter8/11_Q&A_Assistant.py"
    )
    qa_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qa_module)
    PDFLearningAssistant = qa_module.PDFLearningAssistant
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

# 初始化助手
print("\n[2/6] 初始化助手...")
try:
    assistant = PDFLearningAssistant(user_id="e2e_test")
    print("✅ 助手初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    exit(1)

# 加载PDF
print("\n[3/6] 加载测试PDF...")
pdf_path = "/tmp/test_ai_doc.pdf"
try:
    result = assistant.load_document(pdf_path)
    if result["success"]:
        print(f"✅ PDF加载成功")
        print(f"   {result['message']}")
        print(f"   文档: {result['document']}")
    else:
        print(f"❌ PDF加载失败: {result['message']}")
        exit(1)
except Exception as e:
    print(f"❌ PDF加载异常: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试问答
print("\n[4/6] 测试问答功能...")
questions = [
    "什么是机器学习？",
    "Transformer的核心是什么？",
    "大语言模型有哪些特点？"
]

for i, question in enumerate(questions, 1):
    print(f"\n[问题 {i}/{len(questions)}] {question}")
    print("-" * 40)
    try:
        answer = assistant.ask(question, use_advanced_search=True)
        print(f"✅ 回答成功:")
        # 只显示前200个字符
        short_answer = answer.replace("🤖 **智能问答结果**\n\n", "")[:300]
        print(f"   {short_answer}...")
    except Exception as e:
        print(f"❌ 问答失败: {e}")
        import traceback
        traceback.print_exc()

# 测试回顾功能
print(f"\n[5/6] 测试学习回顾...")
try:
    recall_result = assistant.recall("机器学习", limit=3)
    print(f"✅ 回顾成功:")
    print(f"   {recall_result[:200]}...")
except Exception as e:
    print(f"❌ 回顾失败: {e}")

# 获取统计
print(f"\n[6/6] 获取学习统计...")
try:
    stats = assistant.get_stats()
    print("✅ 统计成功:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
except Exception as e:
    print(f"❌ 统计失败: {e}")

print("\n" + "="*60)
print("✨ 端到端测试完成！")
print("="*60)
print("\n💡 提示: 如果LLM响应慢，这是正常的（Nemotron 120B需要约17秒）")
