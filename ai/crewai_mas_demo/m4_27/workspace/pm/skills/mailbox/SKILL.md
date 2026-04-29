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

## 读取邮箱（取走未读消息，原子标记为 in_progress）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py read \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role pm
```

## 发送邮件（任务完成后回报 Manager）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from pm \
    --to manager \
    --type task_done \
    --subject "产品文档已完成" \
    --content "产品文档已写入 /mnt/shared/design/product_spec.md，请验收"
```

## 标记消息完成（处理完后必须调用）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py done \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role pm \
    --msg-id msg-xxxxxxxx
```

## 重要规则

1. 邮件内容只写路径引用，不把文档全文放进邮件
2. 处理完消息后**必须**调用 `done` 命令
3. 只能给团队中存在的角色（manager / pm）发邮件

## 消息类型

| type | 用途 |
|------|------|
| `task_assign` | Manager → PM，分配任务 |
| `task_done`   | PM → Manager，任务完成通知 |
