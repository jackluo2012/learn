"""
team_retro.py — 团队复盘 Skill 脚本（独立运行，无需项目导入）

在沙盒中调用方式：
    pip install openai filelock -q
    python3 /mnt/skills/team-retrospective/scripts/team_retro.py \\
      --logs-dir /mnt/shared/logs \\
      --mailbox-dir /mnt/shared/mailboxes \\
      --manager-id manager \\
      --agent-ids pm,manager \\
      --days 7

输出 JSON（stdout）：
    {"errcode": 0, "errmsg": "success", "bottleneck_agent": "pm", ...}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 输出辅助
# ─────────────────────────────────────────────────────────────────────────────

def _ok(data: dict) -> None:
    print(json.dumps({"errcode": 0, "errmsg": "success", **data}, ensure_ascii=False))
    sys.exit(0)


def _err(code: int, msg: str) -> None:
    print(json.dumps({"errcode": code, "errmsg": msg}, ensure_ascii=False))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 日志读取（内联自 tools/log_ops.py，无需项目导入）
# ─────────────────────────────────────────────────────────────────────────────

def _read_l2(logs_dir: Path, agent_id: str, days: int) -> list[dict]:
    l2_dir = logs_dir / "l2_task"
    if not l2_dir.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results: list[tuple[datetime, dict]] = []
    for f in l2_dir.glob(f"{agent_id}_*.json"):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(record.get("timestamp", ""))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                results.append((ts, record))
        except Exception:
            continue
    results.sort(key=lambda pair: pair[0])
    return [r for _, r in results]


def _read_l1(logs_dir: Path, days: int) -> list[dict]:
    l1_dir = logs_dir / "l1_human"
    if not l1_dir.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results: list[tuple[datetime, dict]] = []
    for f in l1_dir.glob("*.json"):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(record.get("timestamp", ""))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                results.append((ts, record))
        except Exception:
            continue
    results.sort(key=lambda pair: pair[0])
    return [r for _, r in results]


# ─────────────────────────────────────────────────────────────────────────────
# 邮箱写入（内联自 tools/mailbox_ops.py，无需项目导入）
# ─────────────────────────────────────────────────────────────────────────────

def _send_mail(
    mailbox_dir: Path,
    to: str,
    from_: str,
    type_: str,
    subject: str,
    content: str,
) -> str:
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    mailbox_file = mailbox_dir / f"{to}.json"
    msg_id = str(uuid.uuid4())

    try:
        from filelock import FileLock
        lock_ctx = FileLock(str(mailbox_file.with_suffix(".lock")), timeout=10)
    except ImportError:
        import contextlib
        lock_ctx = contextlib.nullcontext()

    with lock_ctx:
        existing: list[dict] = []
        if mailbox_file.exists():
            existing = json.loads(mailbox_file.read_text(encoding="utf-8"))
        existing.append({
            "id":        msg_id,
            "from":      from_,
            "to":        to,
            "type":      type_,
            "subject":   subject,
            "content":   content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read":      False,
        })
        mailbox_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return msg_id


# ─────────────────────────────────────────────────────────────────────────────
# proposals.json 写入
# ─────────────────────────────────────────────────────────────────────────────

def _save_proposals(proposals: list[dict], proposals_file: Path) -> None:
    proposals_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        from filelock import FileLock
        lock_ctx = FileLock(str(proposals_file.with_suffix(".lock")), timeout=10)
    except ImportError:
        import contextlib
        lock_ctx = contextlib.nullcontext()

    with lock_ctx:
        existing: list[dict] = []
        if proposals_file.exists():
            existing = json.loads(proposals_file.read_text(encoding="utf-8"))
        for p in proposals:
            record = dict(p)
            record["proposal_id"] = str(uuid.uuid4())[:8]
            existing.append(record)
        proposals_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 统计与瓶颈识别
# ─────────────────────────────────────────────────────────────────────────────

def _compute_stats(records: list[dict]) -> dict:
    if not records:
        return {"task_count": 0, "avg_quality": None, "failure_rate": None}
    qualities = [r.get("result_quality", 0.0) for r in records]
    failed    = [r for r in records if (r.get("result_quality", 1.0) or 1.0) < 0.5]
    return {
        "task_count":   len(records),
        "avg_quality":  round(sum(qualities) / len(qualities), 3),
        "failure_rate": round(len(failed) / len(records), 3),
    }


def _find_bottleneck(agent_stats: dict[str, dict]) -> str | None:
    eligible = {
        aid: stats
        for aid, stats in agent_stats.items()
        if stats["task_count"] > 0 and stats["avg_quality"] is not None
    }
    if not eligible:
        return None
    return min(eligible, key=lambda aid: eligible[aid]["avg_quality"])


# ─────────────────────────────────────────────────────────────────────────────
# LLM 调用
# ─────────────────────────────────────────────────────────────────────────────

_TEAM_RETRO_SYSTEM_PROMPT = """\
你是一个 Agent 团队复盘分析器（Manager 视角）。根据提供的团队统计摘要，
识别系统性问题并生成团队级改进提案。

## 输出要求

输出合法的 JSON 对象，包含：

{
  "analysis": "2-3句话的宏观诊断（说明最大瓶颈在哪里、为什么）",
  "proposals": [
    {
      "type": "sop_update | tool_fix | soul_update | skill_add",
      "target": "具体文件或协作节点名称",
      "root_cause": "ability_gap | tool_defect | prompt_ambiguity | task_design",
      "current": "当前团队层面的问题",
      "proposed": "具体改动内容",
      "expected_metric": "可测量的团队级预期效果",
      "rollback_plan": "如何回滚",
      "evidence": ["数据依据，如：PM_avg_quality=0.45"],
      "priority": "low | medium | high"
    }
  ]
}

## 注意

- 团队复盘关注**跨 Agent 的系统性问题**（协作摩擦、SOP设计问题），不是追究某个 Agent 的责任
- proposals 可以为空数组（[]），如果统计数据没有明显问题
- evidence 写具体的统计数据值，而不是日志 ID
"""


def _build_team_summary(
    agent_ids:        list[str],
    agent_stats:      dict[str, dict],
    l1_records:       list[dict],
    correction_count: int,
) -> str:
    lines = ["## 团队周报统计摘要\n"]
    lines.append("### Agent 质量指标")
    for aid in agent_ids:
        s = agent_stats.get(aid, {})
        lines.append(
            f"- {aid}: 任务数={s.get('task_count', 0)}, "
            f"平均质量={s.get('avg_quality', 'N/A')}, "
            f"失败率={s.get('failure_rate', 'N/A')}"
        )
    lines.append(f"\n### L1 人类交互")
    lines.append(f"- 纠正事件：{correction_count} 次")
    for r in l1_records[:5]:
        lines.append(f"  [{r.get('type')}] {r.get('subject', '')[:60]}")
    return "\n".join(lines)


def _call_llm(summary_text: str, api_key: str) -> tuple[str, list[dict]]:
    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        model="qwen-max-latest",
        messages=[
            {"role": "system", "content": _TEAM_RETRO_SYSTEM_PROMPT},
            {"role": "user",   "content": summary_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    raw  = response.choices[0].message.content or ""
    data = json.loads(raw)
    return data.get("analysis", ""), data.get("proposals", [])


# ─────────────────────────────────────────────────────────────────────────────
# 主逻辑
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Manager 团队复盘 Skill")
    parser.add_argument("--logs-dir",    required=True, help="日志根目录（/mnt/shared/logs）")
    parser.add_argument("--mailbox-dir", required=True, help="邮箱目录（/mnt/shared/mailboxes）")
    parser.add_argument("--manager-id",  default="manager", help="Manager 的 Agent ID")
    parser.add_argument("--agent-ids",   default="pm,manager",
                        help="参与统计的 Agent ID，逗号分隔，默认 pm,manager")
    parser.add_argument("--days",        type=int, default=7, help="回看天数，默认 7")
    args = parser.parse_args()

    api_key = os.environ.get("ALIYUN_API_KEY", "")
    if not api_key:
        _err(1, "缺少环境变量 ALIYUN_API_KEY")

    logs_dir    = Path(args.logs_dir)
    mailbox_dir = Path(args.mailbox_dir)
    agent_ids   = [aid.strip() for aid in args.agent_ids.split(",") if aid.strip()]

    # ── 1. 统计 L1：人类纠正事件 ─────────────────────────────────────────────
    l1_records       = _read_l1(logs_dir, args.days)
    correction_count = len([r for r in l1_records if "correction" in r.get("type", "")])
    checkpoint_count = len([r for r in l1_records if "checkpoint" in r.get("type", "")])

    # ── 2. 统计各 Agent L2 ───────────────────────────────────────────────────
    agent_stats: dict[str, dict] = {}
    for aid in agent_ids:
        records         = _read_l2(logs_dir, aid, args.days)
        agent_stats[aid] = _compute_stats(records)

    # ── 3. 定位瓶颈 Agent ─────────────────────────────────────────────────────
    bottleneck = _find_bottleneck(agent_stats)
    if bottleneck:
        content = (
            f"Manager 团队复盘发现你是本周质量瓶颈：\n"
            f"  任务数：{agent_stats[bottleneck]['task_count']}\n"
            f"  平均质量分：{agent_stats[bottleneck]['avg_quality']}\n"
            f"  失败率：{agent_stats[bottleneck]['failure_rate']}\n\n"
            f"请触发自我复盘（self-retrospective），分析 L2+L3 日志，\n"
            f"生成改进提案后发至 human.json 等待审批。"
        )
        _send_mail(
            mailbox_dir = mailbox_dir,
            to          = bottleneck,
            from_       = args.manager_id,
            type_       = "retro_trigger",
            subject     = "[团队复盘] 请立即执行自我复盘",
            content     = content,
        )

    # ── 4. 调用 LLM 生成团队级提案 ────────────────────────────────────────────
    summary_text = _build_team_summary(agent_ids, agent_stats, l1_records, correction_count)
    try:
        analysis, raw_proposals = _call_llm(summary_text, api_key)
    except Exception as e:
        _err(2, f"LLM 调用失败：{e}")

    proposals_file = mailbox_dir.parent / "proposals" / "proposals.json"
    if raw_proposals:
        _save_proposals(raw_proposals, proposals_file)

    # ── 5. 发周报给 human.json ────────────────────────────────────────────────
    stats_lines = []
    for aid, s in agent_stats.items():
        stats_lines.append(
            f"  {aid}: 任务数={s['task_count']}, "
            f"平均质量={s.get('avg_quality', 'N/A')}, "
            f"失败率={s.get('failure_rate', 'N/A')}"
        )
    report_content = "\n".join([
        "=== 团队周报 ===\n",
        "【Agent 指标】\n" + "\n".join(stats_lines),
        f"\n【瓶颈 Agent】{bottleneck or '无明显瓶颈'}",
        f"【L1 统计】纠正={correction_count} | checkpoint={checkpoint_count}",
        f"【团队提案数】{len(raw_proposals)} 条（见 proposals.json）",
    ])
    _send_mail(
        mailbox_dir = mailbox_dir,
        to          = "human",
        from_       = args.manager_id,
        type_       = "team_retrospective_report",
        subject     = "[团队周报] Manager 团队复盘完成",
        content     = report_content,
    )

    _ok({
        "agent_stats":          agent_stats,
        "bottleneck_agent":     bottleneck,
        "l1_corrections":       correction_count,
        "l1_checkpoints":       checkpoint_count,
        "team_proposals_count": len(raw_proposals),
        "analysis":             analysis,
    })


if __name__ == "__main__":
    main()
