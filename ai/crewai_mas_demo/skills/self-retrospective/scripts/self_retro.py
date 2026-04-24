"""
self_retro.py — 自我复盘 Skill 脚本（独立运行，无需项目导入）

在沙盒中调用方式：
    pip install openai filelock -q
    python3 /mnt/skills/self-retrospective/scripts/self_retro.py \\
      --logs-dir /mnt/shared/logs \\
      --mailbox-dir /mnt/shared/mailboxes \\
      --agent-id pm \\
      --days 7 \\
      --min-tasks 5

输出 JSON（stdout）：
    {"errcode": 0, "errmsg": "success", "proposals_count": N, "skipped": false}
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
    """读取指定 Agent 在 days 天内的 L2 日志，按 timestamp 升序返回。"""
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


def _read_l3(logs_dir: Path, agent_id: str, task_id: str) -> list[dict]:
    """读取某 Agent 某任务的全部 L3 步骤日志，按 step_idx 升序。"""
    l3_dir = logs_dir / "l3_react" / agent_id / task_id
    if not l3_dir.exists():
        return []
    steps: list[dict] = []
    for f in sorted(l3_dir.glob("step_*.json")):
        try:
            steps.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return steps


def _read_l1(logs_dir: Path, days: int) -> list[dict]:
    """读取 L1 日志（人类交互层）中 days 天内的记录，按 timestamp 升序返回。"""
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
    """写入邮箱 JSON，返回 msg_id。filelock 不可用时退化为无锁写入。"""
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
    """将提案追加写入 proposals.json（不覆盖已有记录）。"""
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
# LLM 调用
# ─────────────────────────────────────────────────────────────────────────────

_SELF_RETRO_SYSTEM_PROMPT = """\
你是一个 Agent 自我复盘分析器。根据提供的日志摘要，生成结构化改进提案。

## 输出要求

必须输出合法的 JSON 对象，格式如下（proposals 数组，1-3条）：

{
  "proposals": [
    {
      "type": "tool_fix | sop_update | soul_update | skill_add",
      "target": "具体文件或方法名，如 pm/skills/design_spec_sop.md",
      "root_cause": "ability_gap | tool_defect | prompt_ambiguity | task_design",
      "current": "当前存在的具体问题",
      "proposed": "具体改动内容（可操作的，不能是模糊描述）",
      "expected_metric": "可测量的预期效果，必须有具体指标，如：checkpoint通过率从45%提升到75%",
      "rollback_plan": "如果效果变差，具体如何回滚",
      "evidence": ["log_id_1", "log_id_2"],
      "priority": "low | medium | high"
    }
  ]
}

## 严格禁止

- proposed 写"下次要更小心"等无效行动
- expected_metric 写模糊描述（必须有可验证的具体指标）
- evidence 为空数组（必须引用至少1条日志）
- root_cause 超出枚举范围（只能是 ability_gap/tool_defect/prompt_ambiguity/task_design）
"""


def _build_log_summary(
    agent_id: str,
    worst_tasks: list[dict],
    l3_data: dict[str, list[dict]],
    l1_related: list[dict],
) -> str:
    lines = [f"## {agent_id} 自我复盘日志摘要\n"]

    lines.append("### 质量最低任务（L2 日志）")
    for r in worst_tasks:
        lines.append(
            f"- task_id={r.get('task_id')} | desc={r.get('task_desc')} "
            f"| quality={r.get('result_quality')} | error={r.get('error_type')}"
        )

    if l3_data:
        lines.append("\n### 失败任务的 ReAct 步骤（L3 日志）")
        for task_id, steps in l3_data.items():
            lines.append(f"\n**{task_id}**（{len(steps)} 步）：")
            failed = [s for s in steps if not s.get("converged", True)]
            for s in (failed or steps)[:5]:
                lines.append(
                    f"  step {s.get('step_idx')}: action={s.get('action')} "
                    f"| obs={str(s.get('observation', ''))[:100]}"
                )

    if l1_related:
        lines.append("\n### 人类纠正记录（L1 日志）")
        for r in l1_related[:5]:
            lines.append(
                f"- [{r.get('type')}] {r.get('subject')} "
                f"| {str(r.get('content', ''))[:100]}"
            )

    return "\n".join(lines)


def _call_llm(log_summary: str, api_key: str) -> list[dict]:
    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        model="qwen-max-latest",
        messages=[
            {"role": "system", "content": _SELF_RETRO_SYSTEM_PROMPT},
            {"role": "user",   "content": log_summary},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    raw = response.choices[0].message.content or ""
    data = json.loads(raw)
    return data.get("proposals", [])


# ─────────────────────────────────────────────────────────────────────────────
# 主逻辑
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 自我复盘 Skill")
    parser.add_argument("--logs-dir",    required=True, help="日志根目录（/mnt/shared/logs）")
    parser.add_argument("--mailbox-dir", required=True, help="邮箱目录（/mnt/shared/mailboxes）")
    parser.add_argument("--agent-id",    required=True, help="Agent 标识，如 pm")
    parser.add_argument("--days",        type=int, default=7,  help="回看天数，默认 7")
    parser.add_argument("--min-tasks",   type=int, default=5,  help="最小样本量，默认 5")
    args = parser.parse_args()

    api_key = os.environ.get("ALIYUN_API_KEY", "")
    if not api_key:
        _err(1, "缺少环境变量 ALIYUN_API_KEY")

    logs_dir    = Path(args.logs_dir)
    mailbox_dir = Path(args.mailbox_dir)

    # ── 1. 样本量检查 ────────────────────────────────────────────────────────
    l2_records = _read_l2(logs_dir, args.agent_id, args.days)
    if len(l2_records) < args.min_tasks:
        _ok({
            "proposals_count": 0,
            "skipped":         True,
            "reason":          f"任务数 {len(l2_records)} < 最小样本量 {args.min_tasks}",
            "proposals":       [],
        })

    # ── 2. 找质量最低的 3 条任务 ─────────────────────────────────────────────
    sorted_records = sorted(l2_records, key=lambda r: r.get("result_quality", 1.0))
    worst_tasks    = sorted_records[:3]
    worst_ids      = [r.get("task_id", "") for r in worst_tasks]

    # ── 3. 读取对应 L3 日志 ───────────────────────────────────────────────────
    l3_data: dict[str, list[dict]] = {}
    for task_id in worst_ids:
        if task_id:
            steps = _read_l3(logs_dir, args.agent_id, task_id)
            if steps:
                l3_data[task_id] = steps

    # ── 4. 读取 L1 中该 Agent 相关的人类纠正记录 ─────────────────────────────
    l1_records = _read_l1(logs_dir, args.days)
    l1_related = [
        r for r in l1_records
        if args.agent_id in r.get("content", "") or args.agent_id in r.get("subject", "")
    ]

    # ── 5. 调用 LLM ───────────────────────────────────────────────────────────
    log_summary = _build_log_summary(args.agent_id, worst_tasks, l3_data, l1_related)
    try:
        raw_proposals = _call_llm(log_summary, api_key)
    except Exception as e:
        _err(2, f"LLM 调用失败：{e}")

    # ── 6. 写入 proposals.json ────────────────────────────────────────────────
    proposals_file = mailbox_dir.parent / "proposals" / "proposals.json"
    if raw_proposals:
        _save_proposals(raw_proposals, proposals_file)

    # ── 7. 发通知至 human.json ────────────────────────────────────────────────
    if raw_proposals:
        summary_lines = []
        for i, p in enumerate(raw_proposals, 1):
            summary_lines.append(
                f"{i}. [{p.get('priority', 'medium')}] {p.get('type')} — {p.get('target')}\n"
                f"   根因：{p.get('root_cause')} | 预期效果：{p.get('expected_metric')}"
            )
        _send_mail(
            mailbox_dir = mailbox_dir,
            to          = "human",
            from_       = "manager",
            type_       = "retrospective_proposal",
            subject     = f"[自我复盘] {args.agent_id} 提交 {len(raw_proposals)} 条改进提案",
            content     = "\n".join(summary_lines),
        )

    _ok({
        "proposals_count": len(raw_proposals),
        "skipped":         False,
        "proposals":       raw_proposals,
    })


if __name__ == "__main__":
    main()
