"""
第28课·数字员工的自我进化（v6）
hooks/l2_task_callback.py — CrewAI task_callback 写 L2 日志

教学要点：
  CrewAI 每完成一个 Task 会调用 task_callback(task_output)。
  通过工厂函数 make_l2_task_callback 闭包绑定 agent_id / logs_dir，
  实现"Task 完成 → L2 自动写入"，替代 run.py 里的手动 write_l2 调用。

v6 变更：
  - 删除 l3_step_callback（L3 由 DigitalWorkerCrew.append_session_raw 承担）
  - 只保留 L2 callback
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from schemas import L2LogRecord
from tools.log_ops import write_l2


def make_l2_task_callback(
    agent_id: str,
    logs_dir: Path,
    quality_scorer: Callable | None = None,
) -> Callable:
    """
    task_callback 工厂：闭包绑定 agent_id + logs_dir。

    CrewAI 在 Task 结束时自动调用返回的回调函数。
    quality_scorer 可选注入：接受 task_output，返回 0.0-1.0 的质量评分。
    默认兜底 0.75。

    用法（在 run.py 中）：
        l2_cb = make_l2_task_callback("pm", LOGS_DIR)
        # 挂到 DigitalWorkerCrew 或 CrewAI Task 的 callback
    """
    def _callback(task_output) -> None:
        task_id = getattr(task_output, "task_id", None) or f"task_{uuid4().hex[:8]}"
        quality = quality_scorer(task_output) if quality_scorer else 0.75

        description_raw = getattr(task_output, "description", None) or ""
        task_desc = str(description_raw)[:200]

        rec = L2LogRecord(
            agent_id=agent_id,
            task_id=task_id,
            task_desc=task_desc,
            result_quality=quality,
            duration_sec=getattr(task_output, "duration_sec", 0.0),
            error_type=getattr(task_output, "error_type", None),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        write_l2(
            logs_dir=logs_dir,
            agent_id=agent_id,
            task_id=task_id,
            record=rec.model_dump(),
        )

    return _callback
