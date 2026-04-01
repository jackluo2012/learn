# Q&A Assistant 配置说明

## ✅ 已配置完成

### LLM 配置 (OpenRouter 免费模型)
- **模型**: `meta-llama/llama-3-8b-instruct:free`
- **API Key**: 已配置
- **Base URL**: https://openrouter.ai/api/v1

### Embedding 配置 (本地免费模型)
- **模型**: `sentence-transformers/all-MiniLM-L6-v2`
- **维度**: 384
- **设备**: CPU

### Qdrant 向量数据库
- **URL**: 云服务
- **集合**: 已重建为 384 维

## 🚀 启动方式

### 方式1：直接运行
```bash
python "chapter8/11_Q&A_Assistant.py"
```

### 方式2：使用启动脚本
```bash
bash chapter8/start_qa.sh
```

## ⚠️ 注意事项

### 1. LLM 限流问题
OpenRouter 免费模型可能遇到限流（429错误）：
- **临时解决**: 等待几分钟后重试
- **永久解决**: 在 https://openrouter.ai/settings/keys 添加你自己的 API Key

添加自己的 Key：
```bash
# 编辑 .env 文件
LLM_API_KEY=你的OpenRouter_API_Key
```

### 2. Embedding 首次加载
- 本地模型首次运行需要下载（约100MB）
- 下载后会缓存到 `~/.cache/huggingface/`
- 后续启动会很快

### 3. GPU 兼容性
- 当前配置强制使用 CPU（避免兼容性问题）
- 如果有兼容的 GPU，可以删除 `.env` 中的 `EMBED_DEVICE=cpu`

## 🔄 切换其他免费模型

编辑 `.env` 文件，修改 `LLM_MODEL_ID`：

```bash
# Llama 3 8B (当前使用)
LLM_MODEL_ID=meta-llama/llama-3-8b-instruct:free

# Llama 3.2 3B
# LLM_MODEL_ID=meta-llama/llama-3.2-3b-instruct:free

# Google Gemma 4B
# LLM_MODEL_ID=google/gemma-3-4b-it:free
```

## 📊 查看可用模型
访问 https://openrouter.ai/models?free=true 查看所有免费模型

## 🧪 测试配置
```bash
python chapter8/test_config.py
```

## ❓ 常见问题

### Q: 提示 "LLM调用失败" 或 429 错误
A: 免费模型限流，等待几分钟后重试，或添加自己的 API Key

### Q: 程序启动很慢
A: 首次加载 embedding 模型需要时间，后续会快很多

### Q: 如何使用中文优化的 embedding 模型
A: 编辑 `.env`，修改为：
```bash
EMBED_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```
然后重建 Qdrant 集合：
```bash
python chapter8/rebuild_qdrant_384.py
```

## 📝 当前配置文件 (.env)
```ini
LLM_MODEL_ID=meta-llama/llama-3-8b-instruct:free
LLM_API_KEY=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
LLM_BASE_URL=https://openrouter.ai/api/v1

EMBED_MODEL_TYPE=local
EMBED_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBED_DEVICE=cpu

QDRANT_VECTOR_SIZE=384
```
