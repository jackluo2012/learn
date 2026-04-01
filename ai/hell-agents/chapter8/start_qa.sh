#!/bin/bash
cd /home/jackluo/my/learn/ai/hell-agents

echo "🚀 启动 Q&A Assistant..."
echo "========================================="

# 设置环境变量
export EMBED_DEVICE=cpu
export CUDA_VISIBLE_DEVICES=""

# 启动程序
python "chapter8/11_Q&A_Assistant.py"
