# LLM 多平台支持架构

## 概述

本模块支持在多个 LLM Provider 之间自由切换，只需修改配置文件，无需改动业务代码。

当前支持的 Provider：
- **aliyun**（默认）：阿里云 DashScope（qwen 系列等）
- **openrouter**：OpenRouter（汇聚 300+ 模型，如 GPT-4o、Claude、Gemini 等）

任何兼容 OpenAI Chat Completions API 的服务均可接入，只需在 `config/llm_config.yaml` 中添加 Provider 定义。

---

## 目录结构

```
crewai_mas_demo/
├── config/
│   ├── __init__.py        # 配置类（LLMConfig），读取 llm_config.yaml
│   └── llm_config.yaml     # 【核心】LLM 配置：Provider 定义、模型列表、角色映射
├── llm/
│   ├── __init__.py         # 导出 create_llm、AliyunLLM 等
│   ├── unified_llm.py      # 【核心】统一工厂函数 create_llm()
│   ├── aliyun_llm.py       # AliyunLLM 实现（向后兼容）
│   └── README.md           # 本文档
├── .env                    # 【核心】所有 API Key 和全局配置
└── .venv/                  # Python 环境
```

---

## 一、配置流程（以 OpenRouter 为例）

### Step 1：在 `.env` 中填入 API Key

```bash
# 阿里云（已有，跳过）
QWEN_API_KEY=sk-b054f82d74d049f1b03f3e1486da74a7

# 新增：OpenRouter（从 https://openrouter.ai/keys 获取）
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **`.env` 中的变量命名规则**：`api_key_env` 的值必须与 `.env` 中的环境变量名一致。
> 例如 `llm_config.yaml` 中写的是 `OPENROUTER_API_KEY`，则 `.env` 中也必须是同名变量。

### Step 2：在 `llm_config.yaml` 中声明 Provider

```yaml
providers:
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key_env: OPENROUTER_API_KEY     # ← 与 .env 中的变量名一致
    extra_headers:
      HTTP-Referer: https://github.com/crewai-mas-demo
      X-Title: crewai-mas-demo
    models:
      - openai/gpt-4o
      - anthropic/claude-sonnet-4-20250514
      - google/gemini-2.5-flash
      - deepseek/deepseek-r1-0528
```

> **base_url 说明**：OpenRouter 的 API 格式与 OpenAI 完全兼容，所有 OpenAI 的调用代码可以直接使用。
> - OpenAI 原站：`https://api.openai.com/v1`
> - OpenRouter：`https://openrouter.ai/api/v1`
> - 阿里云 DashScope 兼容模式：`https://dashscope.aliyuncs.com/compatible-mode/v1`

### Step 3：在 `allowed_models` 中加入新模型

```yaml
allowed_models:
  # ... 现有模型 ...
  - openai/gpt-4o                    # OpenRouter 模型
  - anthropic/claude-sonnet-4-20250514
  - google/gemini-2.5-flash
```

> **allowed_models 是旧接口的白名单**，用于 `llm_config.validate_model()` 检查。新增 Provider 后，模型名必须先加入此列表才能使用。

### Step 4：重启应用，验证

```python
from llm import create_llm

# 验证 OpenRouter 可用
llm = create_llm(model="openai/gpt-4o")
result = llm.call("1+1=?")
print(result)   # 应返回 "2"
```

---

## 二、`.env` 完整配置说明

`.env` 是所有密钥和全局开关的来源，支持多 Provider 共存。

```bash
# ══════════════════════════════════════════
# 全局配置（所有 Provider 共享）
# ══════════════════════════════════════════

# 当前使用的模型（会被 create_llm() 读取作为默认值）
LLM_MODEL_ID=qwen-plus-2025-07-28

# 通用 API Key（Provider 专用 key 未设置时的回退）
LLM_API_KEY=sk-b054f82d74d049f1b03f3e1486da74a7

# 通用端点（Provider 专用端点未设置时的回退）
# 仅在未显式指定 provider 时生效（用于临时重定向到本地代理等）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1


# ══════════════════════════════════════════
# aliyun（阿里云 DashScope）Provider 配置
# llm_config.yaml 中对应：providers.aliyun
# ══════════════════════════════════════════

QWEN_API_KEY=sk-b054f82d74d049f1b03f3e1486da74a7


# ══════════════════════════════════════════
# openrouter Provider 配置
# llm_config.yaml 中对应：providers.openrouter
# ══════════════════════════════════════════

OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# ══════════════════════════════════════════
# 其他 Provider 配置（示例：火山引擎）
# 火山引擎 API Key 从 https://console.volcengine.com/ 获取
# ══════════════════════════════════════════

# ARK_API_KEY=xxxx
# ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 环境变量优先级

```
create_llm(model="openai/gpt-4o") 时：

1. api_key 读取顺序（从上到下，优先用专用 key）
   providers.openrouter.api_key_env
     → OPENROUTER_API_KEY（.env）

2. base_url 读取顺序
   providers.openrouter.base_url
     → （如果 LLM_BASE_URL 存在 且 使用默认 provider）→ LLM_BASE_URL
```

---

## 三、使用方式

### 3.1 基本用法（create_llm）

```python
from llm import create_llm

# 默认：使用 default.text_model（qwen-max），provider=aliyun
llm = create_llm()

# 指定模型名（自动识别 Provider）
llm = create_llm(model="qwen3.5-plus")             # aliyun
llm = create_llm(model="openai/gpt-4o")          # openrouter，自动识别

# 显式指定 Provider
llm = create_llm(model="gpt-4o", provider="openrouter")

# 覆盖配置参数
llm = create_llm(model="qwen3-turbo", temperature=0.3, timeout=300)
```

### 3.2 按角色创建（create_llm_for_role）

```python
from llm import create_llm_for_role

llm = create_llm_for_role("assistant")    # 助手（默认：qwen3.5-plus）
llm = create_llm_for_role("lightweight") # 轻量任务（默认：qwen3-turbo）
llm = create_llm_for_role("vision")      # 视觉任务（默认：qvq-plus）
llm = create_llm_for_role("coder")       # 编程任务（默认：qwen-coder-plus）
llm = create_llm_for_role("long_context")# 长上下文（默认：qwen-long）
```

角色模型可在 `llm_config.yaml` 中自由配置：

```yaml
models:
  assistant:   { model: openai/gpt-4o,        temperature: 0.7 }  # 用 OpenRouter 的 GPT-4o 做助手
  coder:       { model: anthropic/claude-sonnet-4-20250514, temperature: 0.3 }
  vision:      { model: qvq-plus, temperature: 0.7 }
  lightweight: { model: qwen3-turbo,          temperature: 0.3 }
```

### 3.3 在 CrewAI Agent/Crew 中使用

```python
from crewai import Agent
from llm import create_llm, create_llm_for_role

# 单 Agent
agent = Agent(
    role="研究员",
    goal="研究 AI 领域最新进展",
    backstory="你是一名资深 AI 研究员",
    llm=create_llm_for_role("assistant"),  # 推荐
)

# 多 Agent 协作
researcher = Agent(
    role="研究员",
    llm=create_llm(model="openai/gpt-4o"),  # 用 OpenRouter
)
writer = Agent(
    role="写作助手",
    llm=create_llm_for_role("assistant"),
)
```

### 3.4 向后兼容：继续使用 AliyunLLM

已有的代码无需改动，`AliyunLLM` 仍然完全可用：

```python
from llm.aliyun_llm import AliyunLLM

llm = AliyunLLM(model="qwen-plus")
result = llm.call("你好")
```

---

## 四、模型指定格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 纯模型名 | `qwen3.5-plus` | 自动在所有 Provider 中查找该模型 |
| Provider/模型 | `openai/gpt-4o` | 显式指定 Provider，OpenRouter 标准 ID 格式 |
| Provider/模型 | `google/gemini-2.5-flash` | 同上，Gemini 模型 |
| Provider/模型 | `anthropic/claude-sonnet-4-20250514` | 同上，Claude 模型 |

---

## 五、新增 Provider 完整步骤

以接入火山引擎（Volcengine ARK）为例：

**Step 1**：在 `llm_config.yaml` 添加 Provider 定义

```yaml
providers:
  volcengine:
    base_url: https://ark.cn-beijing.volces.com/api/v3
    api_key_env: ARK_API_KEY
    models:
      - doubao-pro-32k
      - doubao-pro-128k
```

**Step 2**：在 `allowed_models` 加入模型

```yaml
allowed_models:
  - doubao-pro-32k
  - doubao-pro-128k
```

**Step 3**：在 `.env` 添加 Key

```bash
ARK_API_KEY=xxxx-xxxx-xxxx-xxxx
```

**Step 4**：使用

```python
from llm import create_llm

llm = create_llm(model="doubao-pro-32k")
result = llm.call("你好")
```

---

## 六、常见问题

### Q: 报错 "Provider 'xxx' 的 API Key 未设置"

原因：`.env` 中未配置对应 Provider 的 API Key，或变量名与 `llm_config.yaml` 中的 `api_key_env` 不一致。

解决：检查 `.env` 中是否有 `OPENROUTER_API_KEY=sk-or-...`（变量名必须完全一致）。

### Q: 报错 "模型 'xxx' 不在允许使用的模型列表中"

原因：模型未加入 `allowed_models`。

解决：在 `llm_config.yaml` 的 `allowed_models` 列表中添加该模型。

### Q: OpenRouter 请求失败（401 Unauthorized）

原因：OpenRouter API Key 未填入 `.env`，或 Key 已过期/额度用尽。

解决：登录 https://openrouter.ai/keys 检查 Key 状态和账户余额。

### Q: 如何临时使用本地代理（如 Ollama）？

```bash
# .env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
```

此时所有不带显式 Provider 前缀的模型请求都会走本地代理。

### Q: 哪些模型在 OpenRouter 上免费？

OpenRouter 有部分 free 模型（无 Key 也能用，但需额外 headers）：

```yaml
providers:
  openrouter:
    models:
      - google/gemma-4-26b-a4b-it:free     # 免费
      - meta-ai/llama-3.2-3b-instruct:free # 免费
```

> 免费模型通常有速率限制，不适合生产环境。

---

## 七、内部实现

```
create_llm(model="openai/gpt-4o")
  │
  ├─ llm_config.resolve_model_provider("openai/gpt-4o")
  │     → provider="openrouter", model="openai/gpt-4o"
  │
  ├─ llm_config.get_provider_base_url("openrouter")
  │     → "https://openrouter.ai/api/v1"
  │
  ├─ llm_config.get_provider_api_key("openrouter")
  │     → os.getenv("OPENROUTER_API_KEY")
  │
  ├─ llm_config.get_provider_extra_headers("openrouter")
  │     → {"HTTP-Referer": "...", "X-Title": "..."}
  │
  └─ CrewAI LLM(
         model="openai/gpt-4o",
         provider="openai",         # CrewAI 原生 OpenAI Completion
         base_url="https://openrouter.ai/api/v1",
         api_key="sk-or-...",
         default_headers={...},
       )
         └─ OpenAI Python SDK
               └─ OpenRouter API（OpenAI 兼容格式）
```

关键点：CrewAI 内置的 `OpenAICompletion` 支持 `base_url` 参数，路由到任何 OpenAI 兼容端点，无需为每个 Provider 单独实现 HTTP 调用。
