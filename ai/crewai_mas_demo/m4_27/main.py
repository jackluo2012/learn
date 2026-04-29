"""
第27课：Human as 甲方 — Manager 入口（v3）

教学对比（v3 vs v2）：
  v2：run_demo.py 编排器 + wait_for_human() 阻塞等待 Human 输入
  v3：Manager 和 PM 各自独立启动，Human 在独立终端通过 human_cli.py 异步确认
      Manager 完成当前能做的事就结束，不阻塞等待 Human

运行方式（三终端协作）：
  # Terminal 1 — Manager 发起项目
  python main.py "帮我把用户注册流程的产品设计做出来"

  # Terminal 2 — Human 查看并确认消息
  python human_cli.py

  # Terminal 1 — Manager 继续（Human 已确认需求后）
  python main.py "需求已确认，请选择 SOP 并分配任务"

  # Terminal 3 — PM 独立工作
  python start_pm.py

  # Terminal 1 — Manager 验收
  python main.py "设计已确认，请审核产品文档"

核心教学点（v3）：
  - 无编排器：Agent 自主决策，靠 Workspace Skill 驱动
  - 异步 Human：human_cli.py 独立运行，Manager 不阻塞
  - 单一接口：只有 Manager 可以向 human.json 发消息（mailbox_cli.py 校验）
"""

from __future__ import annotations

import sys
import os

# 在 crewai 导入之前设置 OPENAI_API_KEY，阻止 CrewAI native provider 报错
os.environ.setdefault("OPENAI_API_KEY", "sk-fake123456789012345678901234567890123456789012345678")

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
SESSION_ID    = "demo_m4l27_manager"


def main() -> None:
    # 获取用户输入，将命令行参数合并为一个字符串并去除首尾空格
    user_request = " ".join(sys.argv[1:]).strip()
    # 如果用户没有输入内容，则使用默认的项目启动指令
    if not user_request:
        user_request = (
            "你是团队的 Manager，请根据你的工作规范（agent.md）开始新项目：\n"
            "宠物健康记录App 产品设计，支持多宠物管理和疫苗提醒。\n\n"
            "请自主决定如何推进项目，使用你的 Skill 来完成任务。"
        )

    # 创建数字工作团队实例，配置工作空间目录、沙盒端口、会话ID等参数
    worker = DigitalWorkerCrew(
        workspace_dir=WORKSPACE_DIR,
        sandbox_port=SANDBOX_PORT,
        session_id=SESSION_ID,
        model="qwen-turbo-1101",
        has_shared=True,
        max_iter=50,  # 增加迭代次数，确保完成所有步骤
    )

    # 打印程序启动信息
    print(f"\n{'='*60}")
    print("第27课：Human as 甲方 — Manager 启动（v3 异步模式）")
    print(f"{'='*60}")
    print(f"Session ID : {SESSION_ID}")
    print(f"Workspace  : {WORKSPACE_DIR}")
    print(f"沙盒端口   : {SANDBOX_PORT}")
    print(f"{'─'*60}")
    print("Human 端请在另一个终端运行：python human_cli.py")
    print(f"{'─'*60}\n")

    # 执行工作团队的任务
    result = worker.kickoff(user_request)

    # 打印执行结果
    print(f"\n{'─'*60}")
    print("Manager 输出：")
    print(result)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()