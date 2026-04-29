"""
第27课：Human as 甲方 — SOP 共创入口（v3）

SOP 共创是独立流程（时点A），在开始正式项目之前运行一次：
  Manager 与 Human 共同设计 SOP 模板，存入 workspace/shared/sop/

注意：
  - 运行前确保 workspace/shared/sop/ 目录存在
  - 本脚本运行后，Human 需要通过 human_cli.py 确认草稿
  - 正式项目通过 main.py 启动

运行方式：
  python sop_setup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 🔥 重要：必须在其他导入之前加载 .env 文件
_M4L27_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L27_DIR.parent

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_file = _PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载环境配置: {env_file}")
    else:
        print(f"⚠️  .env 文件未找到: {env_file}")
except ImportError:
    print("⚠️  python-dotenv 未安装，环境变量可能未加载")
except Exception as e:
    print(f"⚠️  加载 .env 文件时出错: {e}")

for _p in [str(_M4L27_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 应用 CrewAI MCP cleanup 补丁（修复 asyncio.run() 错误）
import crewai_patch  # noqa: E402
crewai_patch.apply_patch()

from shared.digital_worker import DigitalWorkerCrew  # noqa: E402

WORKSPACE_DIR = _M4L27_DIR / "workspace" / "manager"
SANDBOX_PORT  = 8027
SESSION_ID    = "demo_m4l27_sop_setup"
SOP_DIR       = _M4L27_DIR / "workspace" / "shared" / "sop"


def main() -> None:
    # 确保 sop 目录存在
    SOP_DIR.mkdir(parents=True, exist_ok=True)

    user_request = (
        "请使用 sop_creator Skill，与 Human 共同创建一个「产品设计」的标准操作流程（SOP）模板。\n\n"
        "SOP 应包含四要素：\n"
        "1. 角色分工（Manager / PM / Human 各自职责）\n"
        "2. 执行步骤（按顺序，每步有明确输入和输出）\n"
        "3. 检查点（Checkpoint）：哪些环节需要 Human 确认\n"
        "4. 质量标准：每个步骤的验收标准\n\n"
        "完成草稿后，通过 notify_human Skill 通知 Human 审阅（type: sop_draft_confirm）。"
    )

    worker = DigitalWorkerCrew(
        workspace_dir=WORKSPACE_DIR,
        sandbox_port=SANDBOX_PORT,
        session_id=SESSION_ID,
        model="qwen-turbo-1101",
        has_shared=True,
    )

    print(f"\n{'='*60}")
    print("第27课：Human as 甲方 — SOP 共创启动")
    print(f"{'='*60}")
    print(f"SOP 目录   : {SOP_DIR}")
    print(f"沙盒端口   : {SANDBOX_PORT}")
    print(f"{'─'*60}")
    print("Human 端请在另一个终端运行：python human_cli.py")
    print(f"{'─'*60}\n")

    result = worker.kickoff(user_request)

    print(f"\n{'─'*60}")
    print("SOP 共创输出：")
    print(result)
    print(f"{'='*60}")
    print("\n提示：请运行 python human_cli.py 确认 SOP 草稿")


if __name__ == "__main__":
    main()