#!/usr/bin/env python3
"""测试 OpenRouter 免费模型速度"""
import os
import time
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("🚀 OpenRouter 免费模型速度测试")
print("="*60)

# 显示当前配置
print(f"\n📋 当前配置:")
print(f"  模型: {os.getenv('LLM_MODEL_ID')}")
print(f"  API Key: {os.getenv('LLM_API_KEY')[:20]}...")
print(f"  Base URL: {os.getenv('LLM_BASE_URL')}")

# 初始化 LLM
from hello_agents.core.llm import HelloAgentsLLM
llm = HelloAgentsLLM()

# 测试问题列表
test_questions = [
    "你好",
    "什么是机器学习？",
    "用一句话解释Python",
    "Transformer架构的核心是什么？",
]

print("\n" + "="*60)
print("🧪 开始测试...")
print("="*60)

for i, question in enumerate(test_questions, 1):
    print(f"\n[测试 {i}/{len(test_questions)}] 问题: {question}")
    print("-" * 40)

    try:
        # 计时
        start_time = time.time()

        # 调用 LLM
        response = llm.invoke([
            {"role": "system", "content": "你是一个专业的AI助手，请简洁回答问题。"},
            {"role": "user", "content": question}
        ])

        elapsed = time.time() - start_time

        # 显示结果
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)")
        print(f"📝 回答: {response[:200]}{'...' if len(response) > 200 else ''}")

        # 统计
        token_count = len(response)  # 粗略估计
        speed = token_count / elapsed if elapsed > 0 else 0
        print(f"📊 速度: ~{speed:.1f} 字符/秒")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 失败 (耗时: {elapsed:.2f}秒)")
        print(f"   错误: {str(e)[:200]}")

    # 间隔（避免限流）
    if i < len(test_questions):
        print()
        time.sleep(1)

print("\n" + "="*60)
print("✨ 测试完成")
print("="*60)
print("\n💡 提示:")
print("  - 如果遇到 429 错误，说明免费模型被限流")
print("  - 可以等待几分钟后重试")
print("  - 或添加自己的 API Key: https://openrouter.ai/settings/keys")
