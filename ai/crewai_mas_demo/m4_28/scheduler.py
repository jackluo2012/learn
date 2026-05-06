"""
第28课·数字员工的自我进化（v6）
scheduler.py — 极薄 Scheduler（≤40 行有效代码）

职责: cron tick → 双条件判断 → send_mail retro_trigger → 结束
反模式: 不读日志内容 / 不调 LLM / 不打分 / 不装 Agent
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from tools.log_ops import count_l2_since
from tools.mailbox_ops import send_mail

WORKSPACE = Path("workspace/shared")
MIN_GAP_HOURS = 24
MIN_TASK_COUNT = 5


def _last_retro(state_file: Path) -> dict:
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def _update_last(state_file: Path, agent_id: str, ts: str) -> None:
    data = _last_retro(state_file)
    data[agent_id] = ts
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def should_trigger(
    agent_id: str,      # 代理ID，用于标识特定的代理
    logs_dir: Path,     # 日志目录路径，用于存放相关日志文件
    now: datetime | None = None,  # 可选参数，表示当前时间，如果不提供则使用当前UTC时间
    state_file: Path | None = None,  # 可选参数，状态文件的路径，如果不提供则使用默认路径
) -> tuple[bool, str]:  # 返回一个元组，包含布尔值和字符串，表示是否触发及原因
    # 如果未提供当前时间，则设置为当前的UTC时间
    now = now or datetime.now(timezone.utc)
    # 如果未提供状态文件路径，则使用默认的工作空间路径下的".last_retro.json"文件
    sf = state_file or (WORKSPACE / ".last_retro.json")
    # 获取上次触发的时间，并获取指定agent_id的上次触发时间
    last = _last_retro(sf).get(agent_id)
    # 如果上次触发时间存在，且距离当前时间小于最小间隔小时数，则返回False
    if last and (now - datetime.fromisoformat(last)).total_seconds() < MIN_GAP_HOURS * 3600:
        return False, "时间未到"
    # 检查过去24小时内agent_id的任务数量是否小于最小任务数量
    if count_l2_since(logs_dir, agent_id, hours=24) < MIN_TASK_COUNT:
        return False, "任务量不足"
    # 如果以上条件都满足，则返回True，表示可以触发
    return True, "条件满足"


def tick(
    logs_dir: Path,
    mailbox_dir: Path,
    state_file: Path | None = None,
) -> list[str]:
    """执行一次调度检查，返回触发的 agent_id 列表。"""
    now = datetime.now(timezone.utc)
    triggered: list[str] = []
    sf = state_file or (WORKSPACE / ".last_retro.json")
    lock_file = sf.with_suffix(".lock")

    with FileLock(str(lock_file)):
        for agent_id in ("pm", "manager"):
            ok, why = should_trigger(agent_id, logs_dir, now, state_file=sf)
            if not ok:
                continue
            mail_type = "team_retro_trigger" if agent_id == "manager" else "retro_trigger"
            send_mail(
                mailbox_dir=mailbox_dir,
                to=agent_id,
                from_="manager",
                type_=mail_type,
                subject=f"请执行复盘（{why}）",
                content=json.dumps({"reason": "threshold_met", "at": now.isoformat()}),
            )
            _update_last(sf, agent_id, now.isoformat())
            triggered.append(agent_id)

    return triggered


if __name__ == "__main__":
    tick(
        logs_dir=WORKSPACE / "logs",
        mailbox_dir=WORKSPACE / "mailboxes",
    )