# 安全配置指南

本项目包含了敏感信息的最佳实践和安全配置。

## 🚨 紧急措施

如果您的API key已经泄漏，请立即：

1. **撤销所有泄漏的API keys**
   - 阿里云控制台：撤销 `sk-b054f82d74d049f1b03f3e1486da74a7`
   - 百度千帆控制台：撤销 `bce-v3/ALTAK-noOkewWctcjxjWZtW7OlY/...`
   - OpenRouter控制台：撤销 `sk-or-v1-1899a845d2c10f94cfe82d98b4a00fb5...`
   - Qdrant控制台：撤销相关API key
   - Neo4j控制台：更改密码

2. **清理git历史**（参见下文）

## 📋 快速开始

### 1. 初始化环境

```bash
# 运行环境设置脚本
./scripts/setup_env.sh

# 或手动创建.env文件
cp .env.example .env
nano .env  # 编辑.env文件，设置你的API keys
```

### 2. 验证配置

```bash
# 运行配置验证脚本
python scripts/validate_config.py
```

### 3. 安装git安全工具

```bash
# 安装和配置git-secrets
./scripts/git_secrets_setup.sh
```

## 🔒 安全最佳实践

### 环境变量管理

1. **永远不要提交.env文件**
   - `.env`已在`.gitignore`中
   - 使用`.env.example`作为模板

2. **使用不同的API keys**
   - 开发环境：使用测试API keys
   - 生产环境：使用独立的生产API keys
   - 定期轮换API keys（建议每90天）

3. **CI/CD环境**
   - 使用GitHub Secrets或GitLab CI Variables
   - 不要在CI配置中硬编码敏感信息

### Git安全

1. **安装git-secrets**
   ```bash
   ./scripts/git_secrets_setup.sh
   ```

2. **定期扫描git历史**
   ```bash
   # 使用trufflehog
   trufflehog git https://github.com/your-repo.git

   # 使用gitleaks
   gitleaks detect --source . --report-format json
   ```

3. **清理敏感信息**
   - 如果不小心提交了敏感信息，使用git-filter-repo清理
   - 详见 `SECURITY_AUDIT.md`

### 日志安全

1. **日志文件已被忽略**
   - `*.log`在`.gitignore`中
   - 不要提交日志文件

2. **过滤日志中的敏感信息**
   ```python
   import logging

   # 在应用启动时配置
   from scripts.log_security import SensitiveDataFilter
   logging.getLogger().addFilter(SensitiveDataFilter())
   ```

3. **定期清理日志**
   ```bash
   # 删除旧日志
   find . -name "*.log" -mtime +30 -delete
   ```

## 🛠️ 工具脚本

### setup_env.sh

环境设置脚本，用于：
- 创建.env文件
- 验证环境变量
- 检查.gitignore配置

```bash
./scripts/setup_env.sh
```

### validate_config.py

配置验证脚本，检查：
- 必需的环境变量
- API key格式
- .gitignore配置
- 敏感文件跟踪

```bash
python scripts/validate_config.py
```

### git_secrets_setup.sh

Git Secrets安装和配置：
- 安装git-secrets
- 配置敏感模式检测
- 自动阻止敏感信息提交

```bash
./scripts/git_secrets_setup.sh
```

## 📊 安全审计

完整的安全审计报告请参阅：`SECURITY_AUDIT.md`

审计包括：
- 发现的安全问题
- 已采取的措施
- 立即行动项
- 架构调整建议
- 长期维护清单

## 🚨 应急响应

如果发现安全漏洞：

1. **立即撤销泄漏的API keys**
2. **通知团队成员**
3. **检查git历史并清理**
4. **审查访问日志**
5. **更新安全策略**

## 📞 获取帮助

- 完整安全审计：`SECURITY_AUDIT.md`
- 配置验证：`python scripts/validate_config.py`
- 环境设置：`./scripts/setup_env.sh`

## ⚠️ 重要提醒

- **永远不要**提交.env文件
- **永远不要**在代码中硬编码API keys
- **永远不要**在日志中记录敏感信息
- **定期**轮换API keys
- **定期**审计安全配置

---

**最后更新**: 2026-04-27
