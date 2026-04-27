#!/bin/bash
# 环境设置脚本
# 用于安全地设置和管理环境变量

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================"
echo "环境设置脚本"
echo "================================"
echo ""

# 检查.env文件是否存在
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    echo "📝 .env文件不存在，从.env.example创建..."

    if [ ! -f "$ENV_EXAMPLE" ]; then
        echo "❌ 错误: .env.example文件不存在"
        exit 1
    fi

    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "✅ 已创建.env文件"
    echo ""
    echo "⚠️  请编辑.env文件，设置你的API keys："
    echo "   nano .env"
    echo "   或"
    echo "   vim .env"
    echo ""
    exit 0
fi

# 验证.env文件
echo "🔍 验证.env文件..."

# 检查是否有占位符
if grep -q "your_.*_here" "$ENV_FILE"; then
    echo "⚠️  警告: .env文件中仍有占位符需要替换"
    echo ""
    echo "请设置以下环境变量："
    grep "your_.*_here" "$ENV_FILE" | sed 's/^/  /'
    echo ""
fi

# 检查是否有必需的API keys
REQUIRED_VARS=("QWEN_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=your_" "$ENV_FILE"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ 错误: 缺少必需的环境变量:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    exit 1
fi

echo "✅ .env文件验证通过"
echo ""

# 检查.gitignore
echo "🔍 检查.gitignore..."

if ! grep -q "^\.env$" "$PROJECT_ROOT/.gitignore"; then
    echo "⚠️  警告: .gitignore中没有.env"
    echo "   添加.env到.gitignore..."
    echo ".env" >> "$PROJECT_ROOT/.gitignore"
fi

if ! grep -q "^\*\.log$" "$PROJECT_ROOT/.gitignore"; then
    echo "⚠️  警告: .gitignore中没有*.log"
    echo "   添加*.log到.gitignore..."
    echo "*.log" >> "$PROJECT_ROOT/.gitignore"
fi

echo "✅ .gitignore检查完成"
echo ""

# 检查是否有敏感文件被git跟踪
echo "🔍 检查git跟踪的文件..."

cd "$PROJECT_ROOT"

if [ -d ".git" ]; then
    SENSITIVE_TRACKED=$(git ls-files | grep -E "\.env$|\.log$|\.bak$|\.key$|secret" || true)

    if [ -n "$SENSITIVE_TRACKED" ]; then
        echo "❌ 错误: 以下敏感文件被git跟踪:"
        echo "$SENSITIVE_TRACKED" | sed 's/^/  /'
        echo ""
        echo "请运行以下命令从git中移除这些文件:"
        echo "  git rm --cached <filename>"
        echo ""
        exit 1
    fi

    echo "✅ 没有敏感文件被git跟踪"
else
    echo "⚠️  警告: 不是git仓库，跳过git检查"
fi

echo ""
echo "================================"
echo "✅ 环境设置完成！"
echo "================================"
echo ""
echo "下一步:"
echo "  1. 确保.env文件中的API keys已正确设置"
echo "  2. 运行配置验证: python scripts/validate_config.py"
echo "  3. 开始开发: python your_app.py"
echo ""
