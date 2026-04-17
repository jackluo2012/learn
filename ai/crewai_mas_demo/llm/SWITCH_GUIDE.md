# 平台 & 模型切换速查

## 三种切换方式，从简到繁

---

### 方式一：代码中直接指定（最常用）

```python
from llm import create_llm, create_llm_for_role

# ── 指定模型，自动识别平台 ──
llm = create_llm(model="qwen3.5-plus")             # → aliyun
llm = create_llm(model="openai/gpt-4o")          # → openrouter
llm = create_llm(model="google/gemini-2.5-flash") # → openrouter

# ── 显式指定平台 ──
llm = create_llm(model="gpt-4o", provider="openrouter")
llm = create_llm(provider="openrouter")           # 用 openrouter 的默认模型

# ── 按角色创建 ──
llm = create_llm_for_role("assistant")   # → qwen3.5-plus (aliyun)
llm = create_llm_for_role("coder")       # → qwen-coder-plus (aliyun)
```

---

### 方式二：改 `.env` 一行搞定（全局切换）

```bash
# ═══ 全局切换默认平台 ═══
# 默认用 aliyun（不改）
DEFAULT_PROVIDER=aliyun

# 切到 openrouter（所有不带显式 provider 的调用都走 openrouter）
DEFAULT_PROVIDER=openrouter
```

```bash
# ═══ 全局切换默认模型 ═══
LLM_MODEL_ID=qwen3.5-plus          # 默认模型（aliyun）
# LLM_MODEL_ID=openai/gpt-4o       # 切到 GPT-4o（openrouter）

# ═══ 全局覆盖温度/超时 ═══
# LLM_TEMPERATURE=0.3
# LLM_TIMEOUT=300
```

**效果**：改 `.env` 中的 `DEFAULT_PROVIDER`，所有使用 `create_llm()` / `create_llm_for_role()` 且没有显式指定 provider 的代码，自动切到新平台。

---

### 方式三：改 `llm_config.yaml`（角色级别切换）

适合场景：你想让「助手」用 OpenRouter，「编程」继续用阿里云。

```yaml
models:
  assistant:
    model: openai/gpt-4o           # 助手用 GPT-4o（openrouter）
    temperature: 0.7
  coder:
    model: qwen-coder-plus          # 编程继续用阿里云
    temperature: 0.3
  vision:
    model: google/gemini-2.5-flash # 视觉用 Gemini（openrouter）
    temperature: 0.7
  lightweight:
    model: qwen3-turbo              # 轻量任务用阿里云
    temperature: 0.3
  long_context:
    model: qwen-long
    temperature: 0.7
```

---

## 速查表

| 我要… | 改哪里 | 怎么改 |
|-------|--------|--------|
| 临时用一下 GPT-4o | 代码 | `create_llm(model="openai/gpt-4o")` |
| 全部切到 OpenRouter | `.env` | `DEFAULT_PROVIDER=openrouter` |
| 全部切回阿里云 | `.env` | `DEFAULT_PROVIDER=aliyun` |
| 助手用 Claude，其他不变 | `llm_config.yaml` | `models.assistant.model: anthropic/claude-sonnet-4-20250514` |
| 编程用 GPT-4.1 | `llm_config.yaml` | `models.coder.model: openai/gpt-4.1` |
| 临时用本地 Ollama | `.env` | `LLM_BASE_URL=http://localhost:11434/v1` |
| 全局改默认模型 | `.env` | `LLM_MODEL_ID=xxx` |
| 全局改温度 | `.env` | `LLM_TEMPERATURE=0.3` |

---

## 环境变量完整列表

| 变量 | 作用 | 示例 |
|------|------|------|
| `DEFAULT_PROVIDER` | 全局默认平台 | `aliyun` / `openrouter` |
| `LLM_MODEL_ID` | 全局默认模型 | `qwen3.5-plus` / `openai/gpt-4o` |
| `LLM_API_KEY` | 通用 API Key（默认平台回退用） | `sk-xxx` |
| `LLM_BASE_URL` | 通用端点（默认平台回退用） | `https://...` |
| `LLM_TEMPERATURE` | 全局温度覆盖 | `0.3` / `0.7` |
| `LLM_TIMEOUT` | 全局超时覆盖（秒） | `300` / `600` |
| `QWEN_API_KEY` | 阿里云专用 Key | `sk-xxx` |
| `OPENROUTER_API_KEY` | OpenRouter 专用 Key | `sk-or-xxx` |

> **优先级**：代码显式参数 > `.env` 环境变量 > `llm_config.yaml` 配置文件

---

## 当前可用模型

### aliyun（阿里云 DashScope）

| 模型 | 用途 |
|------|------|
| `qwen3.5-plus` | 通用助手（推荐） |
| `qwen3-turbo` | 轻量/快速任务 |
| `qwen-max` | 高质量长文 |
| `qwen-coder-plus` | 编程 |
| `qvq-plus` | 视觉理解 |
| `qwen-long` | 超长上下文 |
| `deepseek-r1` | 推理 |
| `kimi-k2.5` | Kimi |

### openrouter（300+ 模型）

| 模型 | 用途 |
|------|------|
| `openai/gpt-4o` | 通用旗舰 |
| `openai/gpt-4.1` | 编程/指令跟随 |
| `openai/gpt-4.1-mini` | 性价比 |
| `anthropic/claude-sonnet-4-20250514` | 通用/编程 |
| `google/gemini-2.5-flash` | 快速/多模态 |
| `google/gemini-2.5-pro` | 高质量推理 |
| `deepseek/deepseek-r1-0528` | 推理 |
| `deepseek/deepseek-chat` | 通用 |
| `meta-llama/llama-3.3-70b-instruct` | 开源模型 |
| `qwen/qwen3-235b-a22b` | 开源 Qwen |

> 更多模型：https://openrouter.ai/models
