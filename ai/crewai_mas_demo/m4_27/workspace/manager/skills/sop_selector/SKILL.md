---
name: sop_selector
type: task
description: 从 SOP 模板库中选出最匹配当前任务的 SOP，复制为 active_sop.md，通知 Human 确认。
---

# SOP 选择

从 SOP 模板库（`/mnt/shared/sop/`）中选出最匹配当前任务的 SOP。

⚠️ 重要：通过 `skill_loader` 加载本 Skill 后，在沙盒中执行以下命令。

## 前置检查

### 检查 SOP 库是否可用
```bash
ls /mnt/shared/sop/
```

过滤 `draft_` 前缀和 `active_sop.md` 后，如无可用模板，说明 `init_project` 还未运行或 SOP 库未初始化：
- **先加载并运行 `init_project` Skill**，确保共享工作区和 SOP 库已初始化
- 完成后重新执行 `ls /mnt/shared/sop/` 确认模板存在

> ⚠️ 不要报错终止。库为空时自动触发 `init_project`，完成后继续。
> `init_project` 已内置默认 SOP 模板，初始化后即可继续。

## 选择流程（库已有模板时执行）

### Step 1 — 读取需求文档
```bash
cat /mnt/shared/needs/requirements.md
```

### Step 2 — 列出 SOP 库中可用模板
```bash
ls /mnt/shared/sop/
```
**过滤规则**（以下文件不参与选择）：
- `draft_` 前缀的文件（未确认的草稿）
- `active_sop.md`（上次任务的副本，非模板）

### Step 3 — 三步评估选出最匹配的 SOP
1. **需求分析**：从需求文档中提取关键特征（产品类型、规模、技术约束等）
2. **候选评分**：对每个可用模板评分（0-10分），说明理由
3. **推荐**：选出得分最高的，说明选择理由

### Step 4 — 复制为 active_sop.md
```bash
cp /mnt/shared/sop/{选中的模板名}.md /mnt/shared/sop/active_sop.md
```

### Step 5 — 通知 Human 确认（必须执行！）
```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to human \
    --type sop_confirm \
    --subject "SOP 已选定，请确认后继续" \
    --content "选定模板：{模板名}\n理由：{选择理由}\n路径：/mnt/shared/sop/active_sop.md"
```

**验证邮件已发送：**
```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py check-human \
    --mailboxes-dir /mnt/shared/mailboxes \
    --type sop_confirm
```
只有确认 human.json 中有新消息后，才能结束本轮。

## 输出

| 文件 | 说明 |
|------|------|
| `/mnt/shared/sop/active_sop.md` | 本次任务的 SOP（从模板复制） |
| human.json 中新增一条 `sop_confirm` 消息 | 等待 Human 通过 human_cli.py 确认 |
