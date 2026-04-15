"""
多平台 LLM 统一入口

基于 CrewAI 原生 LLM 类实现多 Provider 支持，通过配置文件自由切换。
支持: aliyun (DashScope), openrouter, 以及任何 OpenAI 兼容 API。

核心设计:
- 所有 Provider 走 OpenAI 兼容 API（DashScope / OpenRouter 都是 OpenAI 格式）
- 使用 CrewAI 内置 LLM 类 + base_url 路由，无需自己实现 HTTP 调用
- 保留 AliyunLLM 向后兼容，但推荐使用 create_llm() 工厂函数

用法:
    from llm import create_llm

    # 使用默认 provider 的默认模型
    llm = create_llm()

    # 使用默认 provider 的指定模型
    llm = create_llm(model="qwen3.5-plus")

    # 使用指定 provider 的模型
    llm = create_llm(model="openai/gpt-4o")

    # 使用指定 provider（model 用该 provider 的默认）
    llm = create_llm(provider="openrouter")

    # 显式指定
    llm = create_llm(model="google/gemini-2.5-flash", provider="openrouter")
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from pathlib import Path

# 添加项目根目录到路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import llm_config


def _get_logger():
    """获取模块级 logger。"""
    logger = logging.getLogger("llm.unified_llm")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


logger = _get_logger()


def create_llm(
    model: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
    timeout: int | None = None,
    retry_count: int | None = None,
    **kwargs: Any,
):
    """
    创建 LLM 实例的统一工厂函数。

    根据 model 和 provider 参数，自动解析到正确的 Provider 配置，
    创建 CrewAI 原生 LLM 实例（走 OpenAI 兼容 API）。

    Args:
        model: 模型名称。支持:
            - "qwen3.5-plus": 纯模型名，自动查找 provider
            - "openai/gpt-4o": provider/model 格式，显式指定 provider
            - None: 使用配置文件 default.text_model
        provider: 显式指定 provider 名称。不传则从 model 推断。
        temperature: 采样温度。不传则从配置文件读取。
        timeout: 请求超时（秒）。不传则从配置文件读取。
        retry_count: 重试次数（暂不支持，CrewAI 原生 LLM 自行处理）。
        **kwargs: 传递给 CrewAI LLM 的额外参数（如 base_url, api_key）。

    Returns:
        CrewAI LLM 实例

    Raises:
        ValueError: 模型不在白名单中或 provider 未配置
        ImportError: CrewAI LLM 不可用
    """
    from crewai import LLM as CrewAILLM

    # 1. 解析默认值
    if model is None:
        model = os.getenv("LLM_MODEL_ID") or llm_config.get_default_model()
    
    if temperature is None:
        temperature = llm_config.default_temperature
    
    if timeout is None:
        timeout = llm_config.default_timeout

    # 2. 解析 model → provider
    resolved_provider, resolved_model = llm_config.resolve_model_provider(model)
    
    # 显式 provider 优先
    final_provider = provider or resolved_provider

    # 3. 获取 provider 配置
    base_url = llm_config.get_provider_base_url(final_provider)
    api_key = llm_config.get_provider_api_key(final_provider)
    extra_headers = llm_config.get_provider_extra_headers(final_provider)

    # API Key 回退：仅当使用默认 provider 且 provider 专用 key 未设置时，才用通用 key
    # 跨 provider 的 key 不能互用（如 DashScope 的 key 不能给 OpenRouter）
    if not api_key:
        if final_provider == llm_config.default_provider:
            api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        else:
            raise ValueError(
                f"Provider '{final_provider}' 的 API Key 未设置。"
                f"请在 .env 中设置 {llm_config.get_provider_config(final_provider).get('api_key_env', 'LLM_API_KEY')}，"
                f"或设置通用 LLM_API_KEY 来使用默认 provider。"
            )

    # base_url 回退：仅当使用默认 provider 时，LLM_BASE_URL 才生效
    # 这允许临时切换到其他端点（如本地代理），同时不破坏 provider/model 格式的路由
    env_base_url = os.getenv("LLM_BASE_URL")
    if env_base_url and final_provider == llm_config.default_provider and provider is None:
        base_url = env_base_url

    if not api_key:
        raise ValueError(
            f"Provider '{final_provider}' 的 API Key 未配置。"
            f"请在 .env 中设置 {llm_config.get_provider_config(final_provider).get('api_key_env', 'LLM_API_KEY')}"
        )

    # 4. 验证模型
    llm_config.validate_model(model)

    # 5. 构建 default_headers
    default_headers = dict(extra_headers) if extra_headers else {}

    # 6. 创建 CrewAI LLM 实例
    #    关键: 使用 provider="openai" 让 CrewAI 走 OpenAICompletion（OpenAI 兼容 API）
    #    通过 base_url 路由到实际 provider
    llm = CrewAILLM(
        model=resolved_model,
        provider="openai",
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
        default_headers=default_headers if default_headers else None,
        **kwargs,
    )

    logger.info(
        "create_llm provider=%s model=%s base_url=%s",
        final_provider,
        resolved_model,
        base_url,
    )

    return llm


def create_llm_for_role(
    role: str,
    provider: str | None = None,
    **kwargs: Any,
):
    """
    为特定角色创建 LLM 实例。

    角色定义在 config/llm_config.yaml 的 models 节:
      models:
        assistant:  { model: qwen3.5-plus, temperature: 0.7 }
        lightweight: { model: qwen3-turbo, temperature: 0.3 }
        vision:     { model: qvq-plus, temperature: 0.7 }
        coder:      { model: qwen-coder-plus, temperature: 0.3 }
        long_context: { model: qwen-long, temperature: 0.7 }

    Args:
        role: 角色名（assistant / lightweight / vision / coder / long_context）
        provider: 显式指定 provider
        **kwargs: 传递给 create_llm 的额外参数

    Returns:
        CrewAI LLM 实例
    """
    role_config = llm_config.get_model_config(role)
    model = role_config.get("model", llm_config.get_default_model())
    temperature = role_config.get("temperature", llm_config.default_temperature)

    return create_llm(
        model=model,
        provider=provider,
        temperature=temperature,
        **kwargs,
    )


# ──────────────────────────────────────────────
# 向后兼容: AliyunLLM 仍然可用
# ──────────────────────────────────────────────

def get_aliyun_llm(
    model: str | None = None,
    **kwargs: Any,
):
    """
    创建 AliyunLLM 实例（向后兼容）。

    推荐使用 create_llm() 替代。
    """
    from llm.aliyun_llm import AliyunLLM
    return AliyunLLM(model=model, **kwargs)


if __name__ == "__main__":
    # 测试创建 LLM
    print("=== 测试 create_llm ===")
    
    # 默认模型
    llm = create_llm()
    print(f"默认: model={llm.model}, base_url={getattr(llm, 'base_url', 'N/A')}")
    
    # 指定 aliyun 模型
    llm2 = create_llm(model="qwen3-turbo")
    print(f"qwen3-turbo: model={llm2.model}, base_url={getattr(llm2, 'base_url', 'N/A')}")
    
    # 指定 openrouter 模型（如果配置了 API Key）
    try:
        llm3 = create_llm(model="openai/gpt-4o")
        print(f"openai/gpt-4o: model={llm3.model}, base_url={getattr(llm3, 'base_url', 'N/A')}")
    except ValueError as e:
        print(f"openai/gpt-4o: 跳过（{e}）")
    
    # 角色创建
    llm4 = create_llm_for_role("assistant")
    print(f"assistant: model={llm4.model}")
    
    llm5 = create_llm_for_role("coder")
    print(f"coder: model={llm5.model}")
