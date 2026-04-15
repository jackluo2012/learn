"""
LLM 模块

提供多平台 LLM 支持，通过配置文件自由切换 Provider。

主要组件：
- create_llm(): 统一工厂函数，支持 aliyun / openrouter / 任意 OpenAI 兼容 API
- create_llm_for_role(): 按角色创建 LLM（assistant / vision / coder 等）
- AliyunLLM: 阿里云通义千问 LLM 实现（向后兼容，推荐迁移到 create_llm）

用法:
    from llm import create_llm, create_llm_for_role

    # 默认 provider + 默认模型
    llm = create_llm()

    # 指定模型（自动查找 provider）
    llm = create_llm(model="qwen3.5-plus")

    # 指定 provider 的模型
    llm = create_llm(model="openai/gpt-4o")

    # 按角色创建
    llm = create_llm_for_role("assistant")
"""

from . import aliyun_llm
from .aliyun_llm import AliyunLLM
from .unified_llm import create_llm, create_llm_for_role, get_aliyun_llm

__all__ = [
    "AliyunLLM",
    "aliyun_llm",
    "create_llm",
    "create_llm_for_role",
    "get_aliyun_llm",
]
