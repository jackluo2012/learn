"""
第25课演示：Dev 角色 — 使用通用 DigitalWorkerCrew 框架。

核心教学点：
  同一个 DigitalWorkerCrew 类，换一个 workspace 目录就变成不同角色。
  Dev 的身份、技术权威边界、四段式设计文档格式全部来自 workspace/dev/。
"""

from __future__ import annotations

import sys
from pathlib import Path

_M4L25_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L25_DIR.parent
for _p in [str(_M4L25_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.digital_worker import DigitalWorkerCrew  # noqa: E402

WORKSPACE_DIR = _M4L25_DIR / "workspace" / "dev"
DEMO_INPUT = _M4L25_DIR / "demo_input" / "feature_requirement.md"
SESSION_ID = "demo_m4l25_dev"
SANDBOX_PORT = 8024


def main() -> None:
    if not DEMO_INPUT.exists():
        print(f"[ERROR] 演示输入文件不存在：{DEMO_INPUT}")
        return

    requirement = DEMO_INPUT.read_text(encoding="utf-8")
    user_request = (
        f"请根据以下功能需求，进行技术设计，"
        f"输出 tech_design.md 并保存至 workspace。\n\n{requirement}"
    )

    worker = DigitalWorkerCrew(
        workspace_dir=WORKSPACE_DIR,
        sandbox_port=SANDBOX_PORT,
        session_id=SESSION_ID,
        llmrole="coder",
    )

    print(f"\n{'='*60}")
    print("第25课：团队角色体系 — Dev 演示")
    print(f"{'='*60}")
    print(f"Session ID : {SESSION_ID}")
    print(f"Workspace  : {WORKSPACE_DIR}")
    print(f"沙盒端口   : {SANDBOX_PORT}")
    print(f"{'─'*60}\n")

    result = worker.kickoff(user_request)

    print(f"\n{'─'*60}")
    print("Dev 输出：")
    print(result)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()