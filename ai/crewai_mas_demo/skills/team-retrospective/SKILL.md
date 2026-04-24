---
name: team-retrospective
description: >
  Manager 团队复盘：聚合所有 Agent 的 L2 质量指标，统计 L1 人类纠正事件，
  识别瓶颈 Agent 并触发其自我复盘，调用 LLM 生成团队级改进提案，
  向 human.json 发送周报。
type: task
---

# team-retrospective Skill

## 功能概述

Manager Agent 执行团队复盘时，调用本 Skill 从 Manager 视角分析团队整体状态：

1. 读取 L1 日志，统计人类纠正事件和 checkpoint 退回率
2. 读取所有 Agent 的 L2 日志，按 Agent 计算平均质量分和失败率
3. 定位瓶颈 Agent（质量分最低者），发邮件触发其自我复盘
4. 调用 LLM 生成团队级改进提案（系统性问题，非个人责任）
5. 向 human.json 发送周报

## 调用方式

**脚本路径**：`/mnt/skills/team-retrospective/scripts/team_retro.py`

```bash
# 先确保依赖已安装
pip install openai filelock -q

# 执行团队复盘
python3 /mnt/skills/team-retrospective/scripts/team_retro.py \
  --logs-dir /mnt/shared/logs \
  --mailbox-dir /mnt/shared/mailboxes \
  --manager-id manager \
  --agent-ids pm,manager \
  --days 7
```

**参数说明**：
- `--logs-dir`：日志根目录（固定为 `/mnt/shared/logs`）
- `--mailbox-dir`：邮箱目录（固定为 `/mnt/shared/mailboxes`）
- `--manager-id`：Manager 的 Agent ID（固定为 `manager`）
- `--agent-ids`：参与统计的 Agent ID 列表，逗号分隔（如 `pm,manager`）
- `--days`：回看天数，默认 7

**环境变量**：`ALIYUN_API_KEY`（沙盒已注入）

## 输出格式（JSON）

```json
{
  "errcode": 0,
  "errmsg": "success",
  "agent_stats": {
    "pm":      {"task_count": 8, "avg_quality": 0.612, "failure_rate": 0.375},
    "manager": {"task_count": 3, "avg_quality": 0.883, "failure_rate": 0.0}
  },
  "bottleneck_agent": "pm",
  "l1_corrections": 0,
  "l1_checkpoints": 3,
  "team_proposals_count": 1
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
- `errcode=2`：LLM 调用失败
