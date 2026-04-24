---
name: mailbox-ops
description: >
  数字员工邮箱操作（三态状态机）：send_mail / read_inbox / mark_done / mark_done_all / reset_stale。
  邮箱文件位于共享工作区 /mnt/shared/mailboxes/。
  消息生命周期：unread → in_progress → done。
type: task
---

# mailbox-ops Skill

## 功能概述

本 Skill 提供数字员工之间的邮箱通信能力，基于**三态状态机**：

```
unread → in_progress → done
   ↑         │
   └─────────┘  (reset_stale: 崩溃恢复)
```

- **unread**: 新写入的消息，等待被取走
- **in_progress**: 已被取走，正在处理（防止重复取走）
- **done**: 处理完成（由编排器或 Agent 确认）

邮箱文件路径：`/mnt/shared/mailboxes/{role}.json`

**脚本路径**：`/mnt/skills/mailbox-ops/scripts/mailbox_ops.py`

## 操作规范

### send_mail — 发送消息

```bash
pip install filelock -q

python3 /mnt/skills/mailbox-ops/scripts/mailbox_ops.py send_mail \
  --mailbox-dir /mnt/shared/mailboxes \
  --to pm \
  --from manager \
  --type task_assign \
  --subject "产品文档设计" \
  --content "请根据 /mnt/shared/needs/requirements.md 设计产品规格文档"
```

**参数说明**：
- `--to`：收件人角色（manager | pm | dev | qa）
- `--from`：发件人角色（即你自己）
- `--type`：消息类型（task_assign / task_done / broadcast）
- `--subject`：邮件标题（15字以内）
- `--content`：邮件正文（只传路径引用，不传文档全文）

**输出**：`{"errcode": 0, "errmsg": "success", "msg_id": "<uuid>"}`

### read_inbox — 读取未处理消息

读取 unread 消息并**原子标记为 in_progress**（防止并发重复取走）。
不会直接标 done — 处理成功后需调用 mark_done 确认。

```bash
python3 /mnt/skills/mailbox-ops/scripts/mailbox_ops.py read_inbox \
  --mailbox-dir /mnt/shared/mailboxes \
  --role pm
```

**参数**：`--role` 你自己的角色

**输出**：
```json
{
  "errcode": 0,
  "errmsg": "success",
  "messages": [
    {
      "id": "<uuid>",
      "from": "manager",
      "to": "pm",
      "type": "task_assign",
      "subject": "产品文档设计",
      "content": "请根据需求文档...",
      "timestamp": "2026-04-10T10:00:00+00:00",
      "status": "unread",
      "processing_since": null
    }
  ]
}
```

### mark_done — 确认消息处理完成

将指定消息从 in_progress → done（处理完成确认）。

```bash
python3 /mnt/skills/mailbox-ops/scripts/mailbox_ops.py mark_done \
  --mailbox-dir /mnt/shared/mailboxes \
  --role pm \
  --msg-ids "uuid1,uuid2"
```

**输出**：`{"errcode": 0, "errmsg": "success", "marked": 2}`

### mark_done_all — 批量确认完成

将该角色邮箱中所有 in_progress 消息标记为 done。

```bash
python3 /mnt/skills/mailbox-ops/scripts/mailbox_ops.py mark_done_all \
  --mailbox-dir /mnt/shared/mailboxes \
  --role pm
```

### reset_stale — 崩溃恢复

将超时未完成的 in_progress 消息恢复为 unread。

```bash
python3 /mnt/skills/mailbox-ops/scripts/mailbox_ops.py reset_stale \
  --mailbox-dir /mnt/shared/mailboxes \
  --role pm \
  --timeout 900
```

## ⚠️ 强制执行要求（CRITICAL）

**你必须通过 `sandbox_execute_bash` 实际运行 Python 脚本。**
- 禁止直接返回任何"成功"输出，必须先执行脚本再读取脚本的实际输出
- 禁止根据 task_context 中的 `expected_output` 字段猜测结果
- 执行后必须读取脚本输出的 JSON（含 errcode），将其原文包含在回复中
- 若脚本报错（errcode != 0），必须如实汇报，不得篡改结果

## 错误处理

- 若角色不在允许列表（manager/pm/dev/qa），输出 errcode=1
- 若邮箱文件不存在，自动创建空邮箱后继续
- 若 filelock 获取超时（默认 10 秒），输出 errcode=2
