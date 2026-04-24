---
name: memory-save
description: >
  Use this skill to persist important information from the conversation to
  workspace files so it survives across sessions.

  Activate proactively (without waiting for user to say "remember this") when:
  - User expresses a preference or habit ("I prefer...", "always...", "don't...")
  - User corrects Agent behavior and states how it should work instead
  - A key fact emerges that matters for future sessions (project milestone,
    decision made, important date, contact info)
  - User approves an approach ("let's do it this way going forward")
  - Agent needs to save a work product (report, spec, review result) to workspace

  Do NOT activate for: one-time tasks, Agent's own reasoning, info already in user.md.
allowed-tools:
  - sandbox_file_operations
  - sandbox_execute_code
  - sandbox_execute_bash
---

# memory-save：将内容写入 workspace 文件

## 概述

将内容持久化写入沙盒中的指定文件路径，确保跨 session 保留。

**邮箱文件路径：** `/mnt/shared/mailboxes/{role}.json`（已挂载到沙盒）

### 常用路径说明

| 角色 | 个人工作区路径 | 共享工作区路径 |
|------|-------------|-------------|
| Manager | `/workspace/` | `/mnt/shared/` |
| PM | `/workspace/` | `/mnt/shared/` |

## ❌ 禁止使用的方式（会导致内容截断）

**绝对禁止**通过 `sandbox_execute_bash` 以命令行参数形式传递文件内容：

```bash
# ❌ 错误！shell 遇到引号、反引号、$变量等特殊字符会静默截断
python3 ... --content "大段内容..."
```

**原因**：内容经过 JSON→shell 双重序列化，特殊字符会导致内容被截断，
但程序可能仍然返回 errcode=0，导致无声地写入了残缺内容。

## ✅ 强制使用的方式：sandbox_file_operations write

**必须使用 `sandbox_file_operations(action="write", ...)` 写入文件。**
内容通过 MCP 协议以 JSON 字段直接传递，完全绕过 shell，不存在截断问题。

## ⚠️ 强制执行要求（CRITICAL）

1. **必须调用 `sandbox_file_operations(action="write", ...)` 实际写入文件**
2. 禁止直接返回"成功"，必须先写入再验证
3. 写入后必须 read-back 验证文件大小，确认内容完整
4. 写入字节数为 0 或远小于预期内容长度时，必须视为失败并重试
5. `sandbox_execute_bash` 仅允许用于非内容操作（如 `mkdir -p`、`pip install`），**严禁通过 bash 传递文件内容**

## 执行步骤

### 第一步：直接使用 sandbox_file_operations 写入

调用 `sandbox_file_operations` 工具，参数如下：
- `action`：`"write"`
- `path`：目标文件绝对路径
- `content`：完整文件内容（直接传入多行字符串，无需任何转义）

示例：
```
sandbox_file_operations(
  action="write",
  path="/workspace/review_result.md",
  content="# 验收结论
## 结果：通过
- F-01 用户注册：✅
- F-02 邮件验证：✅
验收日期：2026-04-10"
)
```

### 第二步：read-back 验证（必须执行）

```
sandbox_file_operations(
  action="read",
  path="/workspace/review_result.md"
)
```

- ✅ 文件字节数与内容长度匹配 → 成功
- ❌ 文件内容被截断 → 重试写入

## 示例调用

### Manager 写验收结论

```
sandbox_file_operations(
  action="write",
  path="/workspace/review_result.md",
  content="# 验收结论
## 结果：通过
- F-01 用户注册：✅
- F-02 邮件验证：✅
验收日期：2026-04-10"
)
```

### PM 写产品规格文档

```
sandbox_file_operations(
  action="write",
  path="/mnt/shared/design/product_spec.md",
  content="# 产品规格文档
## 产品概述
...
## 功能规格
F-01: 用户注册
..."
)
```

## 备用方案（仅当 sandbox_file_operations write 不可用时）

> ⚠️ 注意：content 内容中如包含三引号 `"""` 字符，需将其替换为 `\"\"\"`，避免 Python 字符串提前终止。

```
sandbox_execute_code(
  language="python",
  code="""
content = \"\"\"（此处粘贴完整内容）\"\"\"
from pathlib import Path
p = Path("/workspace/review_result.md")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(content, encoding="utf-8")
print(f"写入成功：{p.stat().st_size} 字节")
"""
)
```

**注意**：不得使用 `sandbox_execute_bash` 命令行传递内容，即便是备用方案也禁止。
