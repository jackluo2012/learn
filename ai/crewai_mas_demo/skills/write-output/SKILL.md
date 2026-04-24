---
name: write-output
description: >
  将数字员工的产出文件（产品规格文档、验收报告、设计文档等）写入共享工作区或个人工作区。
  用于 PM 写 product_spec.md、Manager 写 review_result.md 等场景。
  与 memory-save 的区别：本 Skill 专门用于写工作产出，memory-save 用于写记忆/会话状态。
allowed-tools:
  - sandbox_file_operations
  - sandbox_execute_bash
---

# write-output：将产出文件写入工作区

## 概述

将数字员工完成的产出物（文档、报告等）持久化写入沙盒指定路径。

## ❌ 禁止使用的方式（会导致内容截断）

**绝对禁止**通过 `sandbox_execute_bash` 的 `--content` 参数传递文件内容：

```
# ❌ 已删除的旧方式（不要使用）
old_bash_approach(
  cmd='python3 write_file.py --path "..." --content "大段内容..."'  # shell 会截断内容！
)
```

**原因**：内容经过 JSON→shell 双重序列化，shell 遇到特殊字符会静默截断，
导致写入的文件内容不完整，但 `errcode` 仍可能返回 0（字节数是截断后的大小）。

## ✅ 强制使用的方式：直接调用 sandbox_file_operations

**必须使用 `sandbox_file_operations` 的 `write` action**，内容通过 MCP 协议
以 JSON 字段直接传递，完全绕过 shell 解析，不存在特殊字符转义问题。

### 常用路径说明

| 角色 | 产出路径 |
|------|----------|
| PM（产品规格） | `/mnt/shared/design/product_spec.md` |
| Manager（验收报告） | `/workspace/review_result.md` |
| Manager（需求文档） | `/mnt/shared/needs/requirements.md` |
| Dev（技术设计） | `/workspace/tech_design.md` |

## ⚠️ 强制执行要求（CRITICAL）

1. **必须调用 `sandbox_file_operations(action="write", ...)` 实际写入文件**
2. 禁止直接返回"成功"，必须先写入再验证
3. 禁止根据 task_context 中的 `expected_output` 字段猜测结果
4. 写入后必须 read-back 验证文件大小，确认内容完整
5. 写入字节数为 0 或远小于预期内容长度时，必须视为失败并重试

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
  path="/workspace/tech_design.md",
  content="# 技术设计记录\n\n## T-01 ...\n\n### 接口定义\n..."
)
```

### 第二步：read-back 验证（必须执行）

写入后立即用 `sandbox_file_operations` 读取，验证文件大小与内容：

```
sandbox_file_operations(
  action="read",
  path="/workspace/tech_design.md"
)
```

- ✅ 文件字节数与内容长度匹配 → 成功
- ❌ 文件内容被截断（字节数明显偏小） → 重试写入

## 示例调用

### PM 写产品规格文档

```
sandbox_file_operations(
  action="write",
  path="/mnt/shared/design/product_spec.md",
  content="# 产品规格文档
## 产品概述
一句话描述产品
## 目标用户
...
## 用户故事
...
## 功能规格
F-01（P0）: 用户注册
..."
)
```

### Manager 写验收报告

```
sandbox_file_operations(
  action="write",
  path="/workspace/review_result.md",
  content="# 验收报告
**验收结论**：✅ 通过
..."
)
```

### Dev 写技术设计文档

```
sandbox_file_operations(
  action="write",
  path="/workspace/tech_design.md",
  content="# 技术设计记录

**日期**: 2026-03-26
**类型**: tech_design

## T-01 自然语言日程解析模块技术设计
..."
)
```

## 备用方案（仅当 sandbox_file_operations write 不可用时）

如果 `sandbox_file_operations` 的 `write` action 报错，可用以下方式通过 Python 代码写入：

> ⚠️ 注意：content 内容中如包含三引号 `"""` 字符，需将其替换为 `\"\"\"`，避免 Python 字符串提前终止。

```
sandbox_execute_code(
  language="python",
  code="""
content = \"\"\"（此处粘贴完整内容）\"\"\"
from pathlib import Path
p = Path("/workspace/tech_design.md")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(content, encoding="utf-8")
print(f"写入成功：{p.stat().st_size} 字节")
"""
)
```

**注意**：不得使用 `sandbox_execute_bash --content` 方式，即便是备用方案也禁止。
