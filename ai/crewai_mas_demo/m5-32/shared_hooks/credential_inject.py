"""密钥隔离——API Key 在工具执行层注入，LLM 永远看不到。

设计参照：629 次安全测试的最佳实践——模型只看到工具结果，不接触凭证。
"""

import os
from typing import Any

from crewai.tools import BaseTool


class SecureToolWrapper:
    """包装工具，运行时注入凭证。

    用法：
        raw_tool = MyApiTool()
        secure_tool = SecureToolWrapper.wrap(
            raw_tool,
            credentials={"api_key": "API_KEY_ENV_VAR"},
        )
    """

    @staticmethod
    def wrap(
        tool: BaseTool,
        credentials: dict[str, str],
    ) -> BaseTool:
        """包装工具，注入凭证。

        Args:
            tool: 原始 CrewAI 工具
            credentials: {参数名: 环境变量名} 映射
                例：{"api_key": "SEARCH_API_KEY"}

        Returns:
            包装后的工具（对 LLM 透明）
        """
        original_run = tool._run
        resolved = SecureToolWrapper._resolve_credentials(credentials)

        # Protects credentials from LLM context (tool schema), not from
        # in-process Python inspection — use secrets manager for defense-in-depth
        def wrapped_run(**kwargs: Any) -> str:
            merged = {**kwargs, **resolved}
            return original_run(**merged)

        # in-place mutation: BaseTool 是 Pydantic 模型，deep-copy 不可靠
        tool._run = wrapped_run
        return tool

    @staticmethod
    def _resolve_credentials(credentials: dict[str, str]) -> dict[str, str]:
        resolved = {}
        for param_name, env_var in credentials.items():
            value = os.environ.get(env_var, "")
            if not value:
                raise ValueError(
                    f"Credential '{param_name}' requires env var '{env_var}' "
                    f"but it is not set"
                )
            resolved[param_name] = value
        return resolved

    @staticmethod
    def get_credential_status(credentials: dict[str, str]) -> dict:
        """检查凭证状态（不暴露值）。"""
        status = {}
        for param_name, env_var in credentials.items():
            value = os.environ.get(env_var, "")
            status[param_name] = {
                "env_var": env_var,
                "is_set": bool(value),
                "length": len(value) if value else 0,
            }
        return status