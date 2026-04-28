"""
第26课：任务链与信息传递 — PM 入口

PM 独立运行，检查邮箱后自主完成任务：
  1. 加载 mailbox Skill → 读取邮箱
  2. 发现 task_assign → 读取需求文档
  3. 撰写产品文档 → 写入 /mnt/shared/design/product_spec.md
  4. 给 Manager 发 task_done 邮件
  5. 标记原消息为 done

运行方式：
  python start_pm.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_M4L26_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L26_DIR.parent
for _p in [str(_M4L26_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.digital_worker import DigitalWorkerCrew  # noqa: E402

WORKSPACE_DIR = _M4L26_DIR / "workspace" / "pm"
SANDBOX_PORT  = 8026
SESSION_ID    = "demo_m4l26_pm"


def main() -> None:
    user_request = (
        "请检查你的邮箱。如果有新的任务邮件（task_assign），"
        "请按照你的工作规范（agent.md）完成任务。"
    )

    worker = DigitalWorkerCrew(
        workspace_dir=WORKSPACE_DIR,
        sandbox_port=SANDBOX_PORT,
        session_id=SESSION_ID,
        model="glm-5.1",
        has_shared=True,
    )

    print(f"\n{'='*60}")
    print("第26课：任务链与信息传递 — PM 启动")
    print(f"{'='*60}")
    print(f"Session ID : {SESSION_ID}")
    print(f"Workspace  : {WORKSPACE_DIR}")
    print(f"沙盒端口   : {SANDBOX_PORT}")
    print(f"{'─'*60}\n")

    result = worker.kickoff(user_request)

    print(f"\n{'─'*60}")
    print("PM 输出：")
    print(result)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()