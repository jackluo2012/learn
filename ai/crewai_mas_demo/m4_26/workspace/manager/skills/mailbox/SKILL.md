---
name: mailbox
type: task
description: 收发邮件，与团队成员通信。邮箱是数字员工之间的唯一通信渠道。
---

# 邮箱操作

⚠️ 重要：通过 `skill_loader` 加载本 Skill 后，按照下面的命令在沙盒中执行操作。
不要直接调用 `mailbox` 作为工具名——所有操作都通过沙盒 Bash 执行。

邮件脚本位置（沙盒内）：`/workspace/skills/mailbox/scripts/mailbox_cli.py`

## 安装依赖（首次使用前运行一次）

```bash
pip install filelock -q
```

## 发送邮件

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to pm \
    --type task_assign \
    --subject "产品文档设计任务" \
    --content "请阅读 /mnt/shared/needs/requirements.md 并产出产品文档至 /mnt/shared/design/product_spec.md"
```

## 读取邮箱（取走未读消息，原子标记为 in_progress）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py read \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role manager
```

## 标记消息完成（处理完后必须调用）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py done \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role manager \
    --msg-id msg-xxxxxxxx
```

## 崩溃恢复（重置超时消息）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py reset-stale \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role manager \
    --timeout-minutes 15
```

## 重要规则

1. 邮件内容只写路径引用，不把文档全文放进邮件
2. 处理完消息后**必须**调用 `done` 命令，否则消息会被系统认为处理失败并重新投递
3. 只能给团队中存在的角色（manager / pm）发邮件

## 消息类型

| type | 用途 |
|------|------|
| `task_assign` | Manager → 团队成员，分配任务 |
| `task_done`   | 团队成员 → Manager，任务完成通知 |
| `broadcast`   | 全员广播（通知类）|
