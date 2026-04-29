---
name: mailbox
type: task
description: 收发邮件，与团队成员通信。第27课新增：支持向 human.json 发消息（单一接口约束：只有 manager 可以发）。
---

# 邮箱操作（第27课·含 Human 通信）

⚠️ 重要：通过 `skill_loader` 加载本 Skill 后，按照下面的命令在沙盒中执行操作。
不要直接调用 `mailbox` 作为工具名——所有操作都通过沙盒 Bash 执行。

邮件脚本位置（沙盒内）：`/workspace/skills/mailbox/scripts/mailbox_cli.py`

## 安装依赖（首次使用前运行一次）

```bash
pip install filelock -q
```

## 发送邮件（给 PM，三态状态机）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to pm \
    --type task_assign \
    --subject "产品文档设计任务" \
    --content "需求文档：/mnt/shared/needs/requirements.md\nSOP：/mnt/shared/sop/active_sop.md\n输出：/mnt/shared/design/product_spec.md"
```

## 通知 Human（给 human，二态 Schema，单一接口约束）

⚠️ 只有 `--from manager` 才能发给 `--to human`，其他发件人会被拒绝（errcode=1）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to human \
    --type needs_confirm \
    --subject "需求文档（第1轮）待确认" \
    --content "需求文档路径：/mnt/shared/needs/requirements.md"
```

可用的 type 值：
- `needs_confirm`：需求文档待确认
- `sop_draft_confirm`：SOP 草稿待审阅
- `sop_confirm`：SOP 选择待确认
- `checkpoint_request`：阶段性交付物待审核
- `error_alert`：异常上报

## 检查 Human 是否已确认（第27课新增）

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py check-human \
    --mailboxes-dir /mnt/shared/mailboxes \
    --type needs_confirm
```

返回示例：
- 已确认：`{"errcode": 0, "data": {"confirmed": true, "msg_id": "msg-xxx"}}`
- 未确认：`{"errcode": 0, "data": {"confirmed": false, "reason": "Human 尚未确认"}}`
- 已拒绝：`{"errcode": 0, "data": {"confirmed": false, "rejected": true, "human_feedback": "..."}}`

## 读取 Agent 邮箱（取走未读消息，原子标记为 in_progress）

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

## 崩溃恢复

```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py reset-stale \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role manager \
    --timeout-minutes 15
```

## 重要规则（第27课）

1. **单一接口约束**：只有 manager 可以给 human.json 发消息，PM 不能直接联系 Human
2. **Human 邮箱使用二态**：human.json 用 `read: false/true`，而非三态 status
3. **发完通知就结束**：发给 Human 的消息不需要等待回复，Human 通过 human_cli.py 异步确认
4. **邮件内容只写路径引用**，不把文档全文放进邮件
5. **处理完消息后必须调用 `done`**（仅 Agent 邮箱，human.json 不需要）

## 消息类型

| type | 发件方 | 收件方 | 用途 |
|------|--------|--------|------|
| `task_assign` | manager | pm | 分配任务 |
| `task_done` | pm | manager | 任务完成通知 |
| `needs_confirm` | manager | human | 需求文档确认 |
| `sop_draft_confirm` | manager | human | SOP 草稿审阅 |
| `sop_confirm` | manager | human | SOP 选择确认 |
| `checkpoint_request` | manager | human | 阶段性交付物审核 |
| `error_alert` | manager | human | 异常上报 |
