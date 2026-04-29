---
name: requirements_discovery
type: task
description: 需求澄清脚本。分析项目需求，生成需求文档并写入 /mnt/shared/needs/requirements.md。
---

# 需求澄清

当收到新项目需求时，先进行需求澄清，再通知 Human 确认。

## 澄清框架（四维度）

分析收到的需求，识别以下四个维度中哪些信息缺失：

1. **目标**：要解决什么问题？成功标准是什么？
2. **边界**：哪些在范围内？哪些明确不做？
3. **约束**：时间、技术、资源限制？
4. **风险**：已知风险或不确定性？

## 工作流程

### Step 1 — 分析需求
阅读用户的需求描述，识别四个维度中哪些信息已知、哪些缺失。

### Step 2 — 整理澄清内容
根据已知信息，生成需求文档：
- 已知的需求内容直接写入文档
- 缺失的信息标注「待澄清」
- 整理不超过 5 个核心澄清问题（在文档末尾的「待澄清」章节）

### Step 3 — 写入 needs/requirements.md
在沙盒中将需求文档写入共享工作区：
```bash
cat > /mnt/shared/needs/requirements.md << 'EOF'
# 项目需求文档

## 项目背景
（项目描述）

## 目标
（要解决的问题和成功标准）

## 边界
### 范围内
- （功能列表）

### 范围外
- （明确不做的内容）

## 约束
（时间、技术、资源限制）

## 风险
（已知风险或不确定性）

## 待澄清（需 Human 确认）
1. （澄清问题1）
2. （澄清问题2）
EOF
```

## 注意事项

- 需求已经很清晰时，「待澄清」章节可以写「无，需求已明确」，但仍需通知 Human 确认
- 澄清轮次上限：3 轮，超过后在文档中标注「已达最大轮次，依当前理解推进」
- 不要自行猜测和填充不确定的内容——有歧义的点必须标注出来

## 完成后

**🔴 强制要求：必须立即执行以下步骤，不得跳过！**

1. 调用 `notify_human` Skill，发送 needs_confirm 消息给 Human
2. 验证消息已成功发送到 human.json
3. **不要**直接输出 Final Answer，必须先完成通知 Human

**正确流程：**
```bash
# 第1步：发送通知
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \
    --mailboxes-dir /mnt/shared/mailboxes \
    --from manager \
    --to human \
    --type needs_confirm \
    --subject "需求文档（第1轮）待确认" \
    --content "需求文档路径：/mnt/shared/needs/requirements.md"

# 第2步：验证发送成功
python3 /workspace/skills/mailbox/scripts/mailbox_cli.py check \
    --mailboxes-dir /mnt/shared/mailboxes \
    --role human
```

**只有确认消息发送成功后，才能结束本轮工作。**
