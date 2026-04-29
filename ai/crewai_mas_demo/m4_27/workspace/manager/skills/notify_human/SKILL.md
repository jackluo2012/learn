---
name: notify_human
type: reference
description: 通知 Human 在关键节点介入确认。规定何时通知、何时不通知、通知类型和内容格式。
---

# 通知 Human

当需要 Human 介入时（需求确认、SOP 审阅、设计审核、异常上报），通知 Human。

## 重要约束：单一接口原则

**只有 Manager 可以向 human.json 发消息**。

- PM 不能直接联系 Human
- 所有 Human 交互必须经过 Manager 中转
- `mailbox_cli.py` 会强制校验：`--to human --from pm` 会返回 errcode=1

## 通知类型

| type | 触发时机 | 说明 |
|------|---------|------|
| `needs_confirm` | 需求文档写好后 | 请 Human 确认需求是否准确 |
| `sop_draft_confirm` | SOP 草稿完成后 | 请 Human 审阅 SOP 设计 |
| `sop_confirm` | SOP 选择完成后 | 请 Human 确认选定的 SOP |
| `checkpoint_request` | 关键交付物完成后 | 请 Human 审阅产品文档等 |
| `error_alert` | 遇到超出权限的异常 | 上报异常，不可自行处理 |

## 何时通知 Human（必须通知）

- 需求文档完成后（等待 Human 确认方向）
- SOP 选择完成后（等待 Human 确认流程）
- 重要交付物完成时（如产品文档，SOP 规定了 checkpoint）
- 遇到无法自行解决的异常时

## 何时不需要通知 Human（禁止打扰）

- 团队内部任务分配和协调（Manager ↔ PM 邮件往来）
- 常规进度推进（不需要决策的步骤）
- Agent 自己能解决的技术问题

## 通知发送方式

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to human \
    --type {type} \
    --subject "{简洁的主题}" \
    --content "{关键路径 + 1-2句说明}"
```

## 消息内容规范

Human 的时间宝贵。消息要简洁：
- **主题**：直接说明需要确认什么（不超过 15 字）
- **内容**：文件路径 + 1-2 句说明，不要长篇大论

```
# 好的通知 ✅
主题：需求文档（第1轮）待确认
内容：需求文档路径：/mnt/shared/needs/requirements.md

# 差的通知 ❌
主题：请您抽空查看并审阅我们精心整理的需求文档
内容：[把需求文档全文复制进来...]
```

## 发送后

**不要等待 Human 回复**。发完消息，完成当前能做的事，结束本轮。
Human 会在自己方便的时候通过 `human_cli.py` 确认。
下次运行 `main.py` 时，Manager 检查 human.json 的 `read` 字段判断是否已确认。

## 检查 Human 是否已确认

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py check-human \
    --mailboxes-dir /mnt/shared/mailboxes \
    --type needs_confirm
```

返回 `confirmed: true` 表示 Human 已确认，可以继续推进。
