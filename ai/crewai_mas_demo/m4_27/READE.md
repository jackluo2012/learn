# 第27课：Human as 甲方 — 多 Agent 异步协作系统

## 📖 项目简介

这是一个基于 CrewAI 的多 Agent 异步协作系统，模拟了一个完整的产品开发团队：

- **Manager（项目经理）**: 需求澄清、SOP 选择、任务分配、验收
- **PM（产品经理）: 产品设计文档撰写
- **Human（甲方）**: 通过命令行工具异步确认各种决策

### 🎯 教学目标

理解如何构建一个多 Agent 异步协作系统，包括：
- Agent 之间通过邮箱系统通信
- Human 通过独立 CLI 参与决策流程
- 沙盒隔离执行环境
- Workspace-local 技能加载

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    m4_27 多 Agent 协作系统                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Manager    │ ──────> │  Human CLI   │                  │
│  │  (main.py)   │         │(human_cli.py)│                  │
│  │  端口: 8027   │         │              │                  │
│  └──────┬───────┘         └──────────────┘                  │
│         │                                                        │
│         │ task_assign                                          │
│         ↓                                                        │
│  ┌──────────────┐                                              │
│  │     PM       │ ──────> Manager                             │
│  │(start_pm.py) │   task_done                                  │
│  │  端口: 8028   │                                              │
│  └──────────────┘                                              │
│                                                               │
│  共享工作区: /workspace/shared/                               │
│    ├─ mailboxes/         # 邮箱系统                          │
│    ├─ needs/            # 需求文档                           │
│    ├─ design/           # 产品设计文档                        │
│    └─ sop/              # SOP 模板库                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 前置要求

```bash
# 1. Python 环境
Python 3.10+

# 2. Docker 环境（用于 AIO-Sandbox）
docker & docker-compose

# 3. 依赖包
pip install -r requirements.txt
```

### 初始化步骤

```bash
# 1. 进入项目目录
cd /home/jackluo/my/learn/ai/crewai_mas_demo/m4_27

# 2. 配置环境变量（编辑 .env 文件）
# 确保 QWEN_API_KEY 已设置

# 3. 启动沙盒容器
docker-compose -f sandbox-docker-compose.yaml up -d

# 4. 验证系统状态
python diagnose.py

# 5. 初始化邮箱文件（如果是空文件）
echo "[]" > workspace/shared/mailboxes/manager.json
echo "[]" > workspace/shared/mailboxes/pm.json
echo "[]" > workspace/shared/mailboxes/human.json
```

---

## 📋 完整工作流

### 场景：新产品设计项目

#### 第 1 步：Manager 发起项目

**Terminal 1 - Manager**
```bash
python main.py "帮我把宠物健康记录App的产品设计做出来，支持多宠物管理和疫苗提醒"
```

**Manager 会执行：**
1. 初始化共享工作区（`init_project` Skill）
2. 进行需求澄清（`requirements_discovery` Skill）
3. 写入需求文档到 `/mnt/shared/needs/requirements.md`
4. 向 Human 发送确认请求

#### 第 2 步：Human 确认需求

**Terminal 2 - Human（保持运行）**
```bash
python human_cli.py
```

**Human CLI 会：**
1. 显示待确认的消息
2. 等待你的输入（y/n）
3. 如果拒绝，可以提供修改意见

```
📬 收到 1 条新消息：
──────────────────────────────────
  消息 ID：msg-abc123
  类型：需求文档确认
  来自：manager
  主题：需求文档（第1轮）待确认
  内容：需求文档路径：/mnt/shared/needs/requirements.md
──────────────────────────────────
  你的决定
```

#### 第 3 步：Manager 选择 SOP 并分配任务

**Terminal 1 - Manager（Human 确认后）**
```bash
python main.py "需求已确认，请选择 SOP 并分配任务"
```

**Manager 会执行：**
1. 检查 Human 确认状态
2. 从 SOP 库中选择合适的模板（`sop_selector` Skill）
3. 再次请求 Human 确认 SOP 选择

#### 第 4 步：Human 确认 SOP

**Terminal 2 - Human**
```bash
# 在 human_cli.py 中确认 SOP 选择
```

#### 第 5 步：Manager 向 PM 分配任务

**Terminal 1 - Manager**
```bash
python main.py "SOP 已确认，请向 PM 分配任务"
```

**Manager 会执行：**
1. 向 PM 的邮箱发送 `task_assign` 邮件
2. 包含需求文档、SOP、输出路径等信息

#### 第 6 步：PM 执行任务

**Terminal 3 - PM**
```bash
python start_pm.py
```

**PM 会执行：**
1. 检查邮箱，获取任务
2. 读取需求文档和 SOP
3. 撰写产品规格文档
4. 写入 `/mnt/shared/design/product_spec.md`
5. 向 Manager 发送 `task_done` 邮件

#### 第 7 步：Manager 验收

**Terminal 1 - Manager**
```bash
python main.py "设计已完成，请审核产品文档"
```

**Manager 会执行：**
1. 读取 PM 的完成通知
2. （可选）通知 Human 审阅
3. 验收产品文档
4. 写入验收报告到 `/workspace/manager/review_result.md`

---

## 🛠️ 可用命令

### Manager 命令

```bash
# 发起新项目
python main.py "<项目描述>"

# 需求确认后继续
python main.py "需求已确认，请选择 SOP 并分配任务"

# SOP 确认后分配任务
python main.py "SOP 已确认，请向 PM 分配任务"

# 验收产品文档
python main.py "设计已完成，请审核产品文档"
```

### PM 命令

```bash
# PM 启动（检查邮箱并处理任务）
python start_pm.py
```

### Human 命令

```bash
# 交互式模式（推荐）
python human_cli.py

# 只检查是否有新消息
python human_cli.py check

# 对特定消息进行回复
python human_cli.py respond <msg_id> y              # 确认
python human_cli.py respond <msg_id> n "修改意见"   # 拒绝+反馈
```

### SOP 共创命令（可选）

```bash
# 在正式项目前，与 Manager 共同创建 SOP 模板
python sop_setup.py

# 然后在另一个终端运行 human_cli.py 确认草稿
```

---

## 🔧 系统工具

### 诊断工具

```bash
# 全面检查系统状态
python diagnose.py
```

**检查项目：**
- ✅ 环境变量配置
- ✅ 沙盒容器状态
- ✅ MCP 端点连接
- ✅ 工作区结构
- ✅ 邮箱文件格式
- ✅ Skill 加载状态

### 环境测试

```bash
# 测试环境变量和 LLM 配置
python test_env.py
```

---

## 📁 项目结构

```
m4_27/
├── main.py                 # Manager 入口
├── start_pm.py            # PM 入口
├── human_cli.py           # Human 端命令行工具
├── sop_setup.py           # SOP 共创入口
├── sandbox-docker-compose.yaml  # 沙盒容器配置
├── diagnose.py            # 系统诊断工具
├── test_env.py            # 环境测试工具
├── README.md              # 本文件
├── FIXES.md               # 问题修复报告
│
├── workspace/
│   ├── manager/           # Manager 工作区
│   │   ├── agent.md       # Manager 工作规范
│   │   ├── soul.md        # Manager 身份设定
│   │   ├── user.md        # 服务对象画像
│   │   ├── memory.md      # 跨会话记忆索引
│   │   └── skills/        # Manager 专属技能
│   │       ├── load_skills.yaml
│   │       ├── init_project/
│   │       ├── mailbox/
│   │       ├── requirements_discovery/
│   │       ├── sop_creator/
│   │       ├── sop_selector/
│   │       └── notify_human/
│   │
│   ├── pm/                # PM 工作区
│   │   ├── agent.md       # PM 工作规范
│   │   ├── soul.md        # PM 身份设定
│   │   ├── user.md        # 服务对象画像
│   │   ├── memory.md      # 跨会话记忆索引
│   │   └── skills/        # PM 专属技能
│   │       ├── load_skills.yaml
│   │       ├── mailbox/
│   │       └── product_design/
│   │
│   └── shared/            # 共享工作区
│       ├── mailboxes/     # 邮箱系统
│       │   ├── manager.json
│       │   ├── pm.json
│       │   └── human.json
│       ├── needs/         # 需求文档
│       ├── design/        # 产品设计文档
│       └── sop/           # SOP 模板库
```

---

## ⚠️ 常见问题

### 1. 邮箱文件格式错误

**症状：**
```
⚠️ manager.json: 存在但读取失败 (Expecting value: line 1 column 1 (char 0))
```

**解决：**
```bash
echo "[]" > workspace/shared/mailboxes/manager.json
echo "[]" > workspace/shared/mailboxes/pm.json
echo "[]" > workspace/shared/mailboxes/human.json
```

### 2. 沙盒容器未运行

**症状：**
```
❌ 未发现 m4_27 沙盒容器
```

**解决：**
```bash
docker-compose -f sandbox-docker-compose.yaml up -d
```

### 3. API Key 未配置

**症状：**
```
❌ QWEN_API_KEY: 未设置
```

**解决：**
```bash
# 编辑 .env 文件，添加：
QWEN_API_KEY=your-api-key-here
```

### 4. MCP 端点无法访问

**症状：**
```
❌ Manager (端口 8027): 无法访问
```

**解决：**
```bash
# 检查容器状态
docker ps | grep m4_27

# 重启容器
docker-compose -f sandbox-docker-compose.yaml restart
```

### 5. Agent 陷入死循环

**症状：**
```
Agent 一直重复某个动作，无法继续
```

**解决：**
```bash
# 重置超时的邮箱消息
python3 /path/to/mailbox_cli.py reset-stale \
    --mailboxes-dir workspace/shared/mailboxes \
    --role manager \
    --timeout-minutes 15
```

---

## 🔄 重置和清理

### 清空邮箱（重新开始项目）

```bash
echo "[]" > workspace/shared/mailboxes/manager.json
echo "[]" > workspace/shared/mailboxes/pm.json
echo "[]" > workspace/shared/mailboxes/human.json
```

### 重启沙盒容器

```bash
docker-compose -f sandbox-docker-compose.yaml restart
```

### 清理共享工作区

```bash
# 备份重要文件后
rm -rf workspace/shared/needs/*
rm -rf workspace/shared/design/*
```

---

## 📚 核心概念

### 邮箱系统（状态机）

**Agent 邮箱（三态）：**
```
send → unread → read → in_progress → done
```

**Human 邮箱（二态）：**
```
send → read: false → Human 确认 → read: true
```

### 单一接口约束

只有 Manager 可以给 Human 发消息，PM 不能直接联系 Human。

```
✅ Manager → Human
✅ Manager → PM
✅ PM → Manager
❌ PM → Human（被 mailbox_cli.py 拒绝）
```

### Workspace-local Skills

每个角色有自己的 skills 目录：
- Manager: `workspace/manager/skills/`
- PM: `workspace/pm/skills/`

全局 skills（如 `write-output`）会自动回退到 `skills/` 目录。

---

## 🎓 学习要点

1. **异步协作**: Agent 不阻塞等待，Human 通过独立 CLI 确认
2. **邮箱通信**: Agent 之间通过 JSON 文件传递消息
3. **沙盒隔离**: 所有文件操作在 Docker 容器中执行
4. **技能加载**: Workspace-local 优先，全局回退
5. **状态管理**: 三态/二态状态机，FileLock 并发控制

---

## 📝 开发日志

- **2026-04-29**: 修复邮箱文件格式问题，添加诊断工具
- **2026-04-28**: 初始版本，完成 v3 异步架构

---

## 🔗 相关课程

- 第25课：通用数字员工框架
- 第26课：PM 与邮箱协作
- 第27课：Human as 甲方（本课）

---

## 💡 提示

1. **第一次运行前**：确保执行 `diagnose.py` 检查系统状态
2. **多终端协作**：建议使用 3 个终端分别运行 Manager、Human、PM
3. **耐心等待**：LLM 调用和 Skill 执行需要时间，不要中断
4. **查看日志**：Agent 输出中有详细的执行过程，遇到问题先看日志
5. **保存工作**：重要文件会自动写入 workspace，注意备份

---

## 🎉 开始使用

```bash
# 1. 检查系统状态
python diagnose.py

# 2. 确保 Human CLI 准备好（Terminal 2）
python human_cli.py

# 3. 启动 Manager（Terminal 1）
python main.py "帮我把宠物健康记录App的产品设计做出来"

# 4. 根据提示在各个终端中操作
```

**祝使用愉快！** 🚀
