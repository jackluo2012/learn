"""
第26课：任务链与信息传递 — Manager 入口

教学对比（v3 vs v2）：
  v2：需要 run.py 编排器顺序调用 ManagerAssignCrew → PMExecuteCrew → ManagerReviewCrew
  v3：Manager 和 PM 各自独立启动，Agent 基于 workspace-local Skills 自主决策

运行方式：
  # Step 1：Manager 启动（初始化工作区 + 分配任务给 PM）
  python main.py

  # Step 2：PM 启动（检查邮箱 + 完成任务）
  python start_pm.py

  # Step 3：Manager 再次启动（自动检测邮箱 → 验收）
  python main.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_M4L26_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L26_DIR.parent
for _p in [str(_M4L26_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.digital_worker import DigitalWorkerCrew  # noqa: E402

WORKSPACE_DIR   = _M4L26_DIR / "workspace" / "manager"
DEMO_INPUT      = _M4L26_DIR / "demo_input" / "project_requirement.md"
MAILBOX_DIR     = _M4L26_DIR / "workspace" / "shared" / "mailboxes"
SANDBOX_PORT    = 8025
SESSION_ID      = "demo_m4l26_manager"


def _has_pending_task_done() -> bool:
    """检查 Manager 邮箱是否有待处理的 task_done 消息（PM 已完成任务）。"""
    manager_inbox = MAILBOX_DIR / "manager.json"
    if not manager_inbox.exists():
        return False
    try:
        messages = json.loads(manager_inbox.read_text(encoding="utf-8"))
        # 使用any()函数检查messages列表中是否存在符合条件的消息
        return any(
            # 检查消息类型是否为"task_done"并且状态是否为"unread"或"in_progress"
            m.get("type") == "task_done" and m.get("status") in ("unread", "in_progress")
            for m in messages  # 遍历messages列表中的每条消息
        )
    except Exception:
        return False


def _build_user_request() -> str:
    """根据邮箱状态自动决定本轮任务：分配新任务 or 验收 PM 产出。"""
    if _has_pending_task_done():
        # 场景二：PM 已完成，进入验收流程
        return (
            "请检查你的邮箱，你会看到 PM 发来的 task_done 完成通知。"
            "请按照你的工作规范（agent.md）进行验收：\n"
            "1. 读取邮箱中的 task_done 消息\n"
            "2. 读取 /mnt/shared/design/product_spec.md\n"
            "3. 对照 /mnt/shared/needs/requirements.md 进行验收\n"
            "4. 将验收报告写入 /workspace/review_result.md\n"
            "5. 标记消息为 done"
        )
    else:
        # 场景一：新项目，初始化工作区并分配任务
        if not DEMO_INPUT.exists():
            raise FileNotFoundError(f"演示输入文件不存在：{DEMO_INPUT}")
        requirement = DEMO_INPUT.read_text(encoding="utf-8")
        return (
            f"你是团队的 Manager，收到了以下新项目需求，请完成任务分配：\n\n"
            f"{requirement}\n\n"
            f"请按照你的工作规范（agent.md·工作场景一）完成：\n"
            f"1. 初始化共享工作区（init_project Skill）\n"
            f"2. 将需求写入 /mnt/shared/needs/requirements.md\n"
            f"3. 给 PM 发 task_assign 邮件（只传路径引用，不传需求全文）\n"
            f"4. 确认邮件已写入 PM 邮箱"
        )


def main() -> None:
    user_request = _build_user_request()

    # 判断场景用于打印提示
    mode = "【验收模式】" if _has_pending_task_done() else "【分配模式】"

    worker = DigitalWorkerCrew(
        workspace_dir=WORKSPACE_DIR,
        sandbox_port=SANDBOX_PORT,
        session_id=SESSION_ID,
        model="glm-5.1",
        has_shared=True,
    )

    print(f"\n{'='*60}")
    print(f"第26课：任务链与信息传递 — Manager 启动 {mode}")
    print(f"{'='*60}")
    print(f"Session ID : {SESSION_ID}")
    print(f"Workspace  : {WORKSPACE_DIR}")
    print(f"沙盒端口   : {SANDBOX_PORT}")
    print(f"{'─'*60}\n")

    result = worker.kickoff(user_request)

    print(f"\n{'─'*60}")
    print(f"Manager 输出 {mode}：")
    print(result)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()