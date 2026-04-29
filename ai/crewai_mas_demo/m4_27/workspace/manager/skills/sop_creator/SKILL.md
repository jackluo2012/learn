---
name: sop_creator
type: reference
description: 与 Human 共同设计 SOP 模板。基于四要素框架生成草稿，通知 Human 审阅，迭代修改直到确认。
---

# SOP 创建

与 Human 共同设计标准操作流程（SOP）模板，存入 SOP 模板库。

## SOP 四要素框架

设计 SOP 时，必须包含以下四个要素：

1. **角色分工**
   - 哪些角色参与？（Manager / PM / Human）
   - 各自的职责边界是什么？

2. **执行步骤**
   - 按顺序列出操作步骤
   - 每步有明确的输入（Input）和输出（Output）
   - 步骤编号从 1 开始，不跳号

3. **检查点（Checkpoint）**
   - 哪些环节需要 Human 确认才能继续？
   - 每个 Checkpoint 的触发条件是什么？
   - Human 确认 / 拒绝后分别怎么处理？

4. **质量标准**
   - 每个步骤的验收标准（可量化 / 可验证）
   - 最终交付物的验收条件

## 工作流程

### Step 1 — 生成 SOP 草稿
基于四要素框架，在沙盒中生成 SOP 草稿：
```bash
cat > /mnt/shared/sop/draft_{名称}.md << 'EOF'
# {名称} 标准操作流程（SOP）

## 角色分工
| 角色 | 职责 |
|------|------|
| Manager | ... |
| PM | ... |
| Human | ... |

## 执行步骤
| 步骤 | 执行者 | 操作 | 输入 | 输出 |
|------|--------|------|------|------|
| 1 | Manager | ... | ... | ... |
| 2 | ... | ... | ... | ... |

## 检查点（Human 确认节点）
| 检查点 | 触发时机 | 确认内容 |
|--------|---------|---------|
| CP1 | 需求文档完成后 | 需求是否准确完整 |
| CP2 | ... | ... |

## 质量标准
| 交付物 | 验收标准 |
|--------|---------|
| 需求文档 | 包含目标/边界/约束/风险四维度 |
| 产品文档 | 包含用户故事和验收标准 |
EOF
```

### Step 2 — 通知 Human 审阅
```bash
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to human \
    --type sop_draft_confirm \
    --subject "产品设计 SOP 草稿待审阅" \
    --content "SOP 草稿路径：/mnt/shared/sop/draft_product_design_sop.md\n请通过 human_cli.py 确认"
```

### Step 3 — 等待 Human 反馈
发完消息后结束本轮。Human 通过 `human_cli.py` 确认后，下次运行时检查 human.json 状态。

## 草稿命名规范

- 草稿：`draft_{功能名称}_{版本}.md`（如 `draft_product_design_sop.md`）
- 确认后重命名：`{功能名称}_sop.md`（如 `product_design_sop.md`）
- 不得使用 `active_sop.md` 作为草稿名（该名称保留给当次任务选定的 SOP）
