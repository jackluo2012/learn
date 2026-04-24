---
name: self-retrospective
description: >
  Agent 自我复盘：读取 L2/L3/L1 日志，调用 LLM 生成结构化改进提案，
  写入 proposals.json 并发通知至 human.json 等待审批。
  适用场景：Agent 在完成足够多任务后，触发自我评估和改进提案生成。
type: task
---

# self-retrospective Skill

## 功能概述

PM Agent 执行自我复盘时，调用本 Skill 分析历史日志并生成结构化改进提案：

1. 读取 L2 日志，找出质量最低的任务
2. 读取对应 L3 日志，找到具体失败节点
3. 读取 L1 中相关的人类纠正记录
4. 调用 LLM 生成结构化改进提案（Pydantic schema 约束）
5. 写入 `/mnt/shared/proposals/proposals.json`
6. 发通知至 `/mnt/shared/mailboxes/human.json` 等待审批

## 调用方式

**脚本路径**：`/mnt/skills/self-retrospective/scripts/self_retro.py`

```bash
# 先确保依赖已安装
pip install openai filelock -q

# 执行自我复盘
python3 /mnt/skills/self-retrospective/scripts/self_retro.py \
  --logs-dir /mnt/shared/logs \
  --mailbox-dir /mnt/shared/mailboxes \
  --agent-id pm \
  --days 7 \
  --min-tasks 5
```

**参数说明**：
- `--logs-dir`：日志根目录（固定为 `/mnt/shared/logs`）
- `--mailbox-dir`：邮箱目录（固定为 `/mnt/shared/mailboxes`）
- `--agent-id`：执行复盘的 Agent 标识（如 `pm`）
- `--days`：回看天数，默认 7
- `--min-tasks`：最小样本量阈值，低于此值跳过复盘，默认 5

**环境变量**：`ALIYUN_API_KEY`（沙盒已注入）

## 输出格式（JSON）

```json
{
  "errcode": 0,
  "errmsg": "success",
  "proposals_count": 2,
  "skipped": false,
  "proposals": [
    {
      "type": "sop_update",
      "target": "pm/sop/design_spec_sop.md",
      "root_cause": "prompt_ambiguity",
      "current": "验收标准缺少移动端适配要求",
      "proposed": "在 SOP 验收清单中增加「移动端响应式」检查项",
      "expected_metric": "checkpoint 通过率从 45% 提升到 75%",
      "rollback_plan": "删除新增检查项，恢复原 SOP",
      "evidence": ["t001", "t003"],
      "priority": "high"
    }
  ]
}
```

样本量不足时：
```json
{
  "errcode": 0,
  "errmsg": "success",
  "proposals_count": 0,
  "skipped": true,
  "reason": "任务数 3 < 最小样本量 5"
}
```

## ⚠️ 强制执行要求（CRITICAL）

**你必须通过 `sandbox_execute_bash` 实际运行 Python 脚本。**
- 禁止直接返回任何"成功"输出，必须先执行脚本再读取脚本的实际输出
- 禁止根据 task_context 中的 `expected_output` 字段猜测结果
- 执行后必须读取脚本输出的 JSON（含 errcode），将其原文包含在回复中
- 若脚本报错（errcode != 0），必须如实汇报，不得篡改结果

## 错误处理

- `errcode=1`：缺少 `ALIYUN_API_KEY` 环境变量
- `errcode=2`：LLM 调用失败（网络、API Key 无效等）
- `skipped=true`：样本量不足，非错误，正常跳过
