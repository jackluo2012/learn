"""
配置模块

提供统一的配置管理，包括 LLM 模型配置。
"""
import os
from pathlib import Path
from typing import Any

import yaml


class LLMConfig:
    """LLM 配置管理类"""
    
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
        # 合并默认配置
        default_config = self._config.get("default", {}).copy()
        default_config.update(config)
        return default_config
    
    def is_model_allowed(self, model: str) -> bool:
        """检查模型是否在白名单中"""
        allowed = self._config.get("allowed_models", [])
        return model in allowed
    
    def validate_model(self, model: str) -> None:
        """验证模型是否允许使用，不允许则抛出异常"""
        if not self.is_model_allowed(model):
            raise ValueError(
                f"模型 '{model}' 不在允许使用的模型列表中。"
                f"请在 config/llm_config.yaml 的 allowed_models 中添加此模型，"
                f"或从以下模型中选择: {', '.join(self._config.get('allowed_models', []))}"
            )
    
    @property
    def allowed_models(self) -> list:
        """获取所有允许的模型列表"""
        return self._config.get("allowed_models", [])
    
    @property
    def default_region(self) -> str:
        """获取默认地域"""
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


# 全局配置实例
llm_config = LLMConfig()

__all__ = ["LLMConfig", "llm_config"]
