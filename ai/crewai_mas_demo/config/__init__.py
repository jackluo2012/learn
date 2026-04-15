"""
配置模块

提供统一的配置管理，包括 LLM 模型配置、多 Provider 支持。
自动加载项目根目录的 .env 文件，无需手动 setup()。
"""
import os
from pathlib import Path
from typing import Any

import yaml

# ── 自动加载 .env ──────────────────────────────────────────────────────────
# 查找项目根目录（向上找到包含 .env 的目录）
_config_dir = Path(__file__).resolve().parent
for _root in (_config_dir, _config_dir.parent, _config_dir.parent.parent):
    _env_file = _root / ".env"
    if _env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_env_file, override=True)
        except ImportError:
            pass
        break


class LLMConfig:
    """LLM 配置管理类，支持多 Provider。"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent / "llm_config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    # ──────────────────────────────────────────
    # Provider 相关
    # ──────────────────────────────────────────
    
    @property
    def default_provider(self) -> str:
        """获取默认 provider 名称"""
        return self._config.get("default", {}).get("provider", "aliyun")
    
    def get_provider_config(self, provider: str | None = None) -> dict:
        """获取指定 provider 的配置，不传则用 default.provider"""
        name = provider or self.default_provider
        providers = self._config.get("providers", {})
        if name not in providers:
            raise ValueError(
                f"Provider '{name}' 未配置。"
                f"可用: {', '.join(providers.keys())}"
            )
        return providers[name]
    
    def get_provider_base_url(self, provider: str | None = None) -> str:
        """获取 provider 的 base_url"""
        cfg = self.get_provider_config(provider)
        return cfg.get("base_url", "")
    
    def get_provider_api_key(self, provider: str | None = None) -> str | None:
        """从环境变量读取 provider 的 API Key"""
        cfg = self.get_provider_config(provider)
        env_name = cfg.get("api_key_env", "")
        if not env_name:
            return None
        return os.getenv(env_name)
    
    def get_provider_extra_headers(self, provider: str | None = None) -> dict:
        """获取 provider 的额外 headers"""
        cfg = self.get_provider_config(provider)
        return cfg.get("extra_headers", {})
    
    def get_provider_models(self, provider: str | None = None) -> list[str]:
        """获取 provider 下的模型列表"""
        cfg = self.get_provider_config(provider)
        return cfg.get("models", [])
    
    def get_all_provider_models(self) -> dict[str, list[str]]:
        """获取所有 provider 及其模型列表 {provider: [models]}"""
        result = {}
        for name, cfg in self._config.get("providers", {}).items():
            result[name] = cfg.get("models", [])
        return result
    
    def resolve_model_provider(self, model: str) -> tuple[str, str]:
        """
        解析模型所属的 provider。
        
        支持两种格式:
        - "provider/model": 显式指定 provider
        - "model": 自动查找包含该模型的 provider
        
        Returns:
            (provider_name, model_name_without_prefix)
        """
        if "/" in model:
            # 显式 provider 前缀，如 "openai/gpt-4o"
            prefix, _, model_part = model.partition("/")
            # 检查 prefix 是否是已注册的 provider
            providers = self._config.get("providers", {})
            if prefix in providers:
                return prefix, model_part
            # 否则可能是模型名本身包含 "/"（如 qwen3-235b-a22b），走自动查找
            # 但 OpenRouter 模型都带 "/"，所以先查找
            for pname, pcfg in providers.items():
                if model in pcfg.get("models", []):
                    return pname, model
        
        # 自动查找: 遍历所有 provider，找到包含该模型的
        for pname, pcfg in self._config.get("providers", {}).items():
            if model in pcfg.get("models", []):
                return pname, model
        
        # 未找到，返回默认 provider
        return self.default_provider, model
    
    # ──────────────────────────────────────────
    # 默认模型（向后兼容）
    # ──────────────────────────────────────────
    
    def get_default_model(self) -> str:
        """获取默认文本模型"""
        return self._config.get("default", {}).get("text_model", "qwen-max")
    
    def get_default_image_model(self) -> str:
        """获取默认多模态模型"""
        return self._config.get("default", {}).get("image_model", "qwen3-vl-plus")
    
    def get_default_summary_model(self) -> str:
        """获取默认摘要模型"""
        return self._config.get("default", {}).get("summary_model", "qwen3-turbo")
    
    def get_model_config(self, model_type: str) -> dict:
        """获取特定类型的模型配置"""
        models = self._config.get("models", {})
        config = models.get(model_type, {})
        default_config = self._config.get("default", {}).copy()
        default_config.update(config)
        return default_config
    
    # ──────────────────────────────────────────
    # 白名单校验（向后兼容 + 多 provider 扩展）
    # ──────────────────────────────────────────
    
    def is_model_allowed(self, model: str) -> bool:
        """检查模型是否在白名单中（兼容旧 allowed_models 和新 providers.models）"""
        # 先查旧白名单
        allowed = self._config.get("allowed_models", [])
        if model in allowed:
            return True
        # 再查所有 provider 的模型列表
        for pcfg in self._config.get("providers", {}).values():
            if model in pcfg.get("models", []):
                return True
        return False
    
    def validate_model(self, model: str) -> None:
        """验证模型是否允许使用，不允许则抛出异常"""
        if not self.is_model_allowed(model):
            # 收集所有可用模型
            all_models = list(self._config.get("allowed_models", []))
            for pcfg in self._config.get("providers", {}).values():
                all_models.extend(pcfg.get("models", []))
            raise ValueError(
                f"模型 '{model}' 不在允许使用的模型列表中。"
                f"请在 config/llm_config.yaml 中添加此模型，"
                f"或从以下模型中选择: {', '.join(sorted(set(all_models)))}"
            )
    
    @property
    def allowed_models(self) -> list:
        """获取所有允许的模型列表（合并旧白名单 + 各 provider 模型）"""
        result = list(self._config.get("allowed_models", []))
        for pcfg in self._config.get("providers", {}).values():
            result.extend(pcfg.get("models", []))
        return sorted(set(result))
    
    @property
    def default_region(self) -> str:
        """获取默认地域（仅 aliyun 使用）"""
        return self._config.get("default", {}).get("region", "cn")
    
    @property
    def default_temperature(self) -> float:
        """获取默认温度"""
        return self._config.get("default", {}).get("temperature", 0.7)
    
    @property
    def default_retry_count(self) -> int:
        """获取默认重试次数"""
        return self._config.get("default", {}).get("retry_count", 2)
    
    @property
    def default_timeout(self) -> int:
        """获取默认超时时间"""
        return self._config.get("default", {}).get("timeout", 600)
    
    @property
    def providers(self) -> dict:
        """获取所有 provider 配置"""
        return self._config.get("providers", {})


# 全局配置实例
llm_config = LLMConfig()

__all__ = ["LLMConfig", "llm_config"]
