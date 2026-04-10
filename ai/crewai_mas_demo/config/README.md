# LLM 配置管理说明

本项目所有大模型调用都通过配置文件 `config/llm_config.yaml` 进行管理。

## 配置结构

```yaml
default:          # 默认配置
  text_model:     # 默认文本模型
  image_model:    # 默认多模态模型
  summary_model:  # 默认摘要模型
  region:         # 默认地域
  temperature:    # 默认温度
  retry_count:    # 默认重试次数
  timeout:        # 默认超时时间

models:           # 特定用途模型配置
  assistant:      # 主助手模型
  lightweight:    # 轻量级模型
  vision:         # 视觉模型
  coder:          # 代码模型
  long_context:   # 长文本模型

allowed_models:   # 模型白名单
```

## 使用方式

### 1. 基本使用（推荐）

```python
from llm.aliyun_llm import AliyunLLM

# 所有参数从配置文件读取
llm = AliyunLLM()
```

### 2. 覆盖特定参数

```python
from llm.aliyun_llm import AliyunLLM

# 覆盖温度参数，其他从配置文件读取
llm = AliyunLLM(temperature=0.3)
```

### 3. 使用特定类型模型

```python
from llm.aliyun_llm import AliyunLLM
from config import llm_config

# 获取轻量级模型配置
config = llm_config.get_model_config("lightweight")
llm = AliyunLLM(
    model=config["model"],
    temperature=config["temperature"]
)
```

## 模型白名单

所有模型必须在 `allowed_models` 白名单中才能使用。如果尝试使用不在白名单中的模型，会抛出 `ValueError`。

### 添加新模型到白名单

1. 编辑 `config/llm_config.yaml`
2. 在 `allowed_models` 列表中添加模型名称
3. 确保该模型在你的阿里云账号中有可用额度

## 环境变量优先级

环境变量可以覆盖配置文件中的设置：

- `LLM_MODEL_ID`: 覆盖默认文本模型
- `QWEN_API_KEY` / `DASHSCOPE_API_KEY`: API 密钥
- `LLM_RETRY_COUNT`: 覆盖重试次数

优先级：传入参数 > 环境变量 > 配置文件

## 当前配置的模型

根据配额数据，以下模型已配置：

### 高额度模型（推荐）
- `qwen-max` - 旗舰模型，仅使用 1.53%
- `qwen-plus` - 高级模型，使用 66.15%
- `qwen-turbo` - 快速模型，100% 额度
- `qwen3-max` - 新一代旗舰，使用 96.46%
- `qwen3-turbo` - 新一代快速模型，100% 额度
- `qwen3-vl-plus` - 多模态模型，使用 96%
- `deepseek-r1` - DeepSeek 推理模型，100% 额度
- `kimi-k2.5` - Moonshot 模型，100% 额度

### 专用模型
- `qwen-long` - 长文本处理（200K 上下文）
- `qwen-coder-plus` - 代码生成
- `qwen-vl-plus` - 视觉理解

## 修改配置

修改 `llm_config.yaml` 后，配置会自动生效，无需重启服务。
