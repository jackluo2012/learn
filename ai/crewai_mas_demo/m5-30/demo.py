"""F10: 单 Agent Demo —— Bootstrap + SkillLoader + Hook 框架 + Langfuse 全链路追踪。

演示架构（复用 25 课框架）：
  - build_bootstrap_prompt()：加载 workspace 四件套（soul / user / agent / memory）
  - SkillLoaderTool：渐进式披露，task 型 Skill 启动 Sub-Crew 在沙盒中执行
  - Hook 框架（两层加载）+ Langfuse OTel 追踪
  - 💡 全局 Hook（@before_llm_call 等）自动传播到 Sub-Crew

前置条件：
    docker compose -f sandbox-docker-compose.yaml up -d

运行方式：
    python3 demo.py
    python3 demo.py "为一个短链接服务产出技术设计文档"
"""

from __future__ import annotations

import atexit
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_M5L30_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M5L30_DIR.parent
for _p in [str(_M5L30_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 💥 重要：必须在导入任何模块之前设置环境变量
# 先加载 .env，然后确保 QWEN_API_KEY 也被设置（因为 llm_config 使用 QWEN_API_KEY）
from dotenv import load_dotenv
load_dotenv(_M5L30_DIR / ".env", override=True)

# 确保 QWEN_API_KEY 被设置（llm_config.get_provider_api_key('aliyun') 会读取这个变量）
if not os.environ.get("QWEN_API_KEY"):
    os.environ["QWEN_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")

print("=== 所有环境变量 ===")
for key, value in os.environ.items():
    print(f"{key} = {value}")

from crewai import Agent, Crew, LLM, Task

from m3_20.m3_20_file_memory import build_bootstrap_prompt
from tools.skill_loader_tool import SkillLoaderTool

from hook_framework import (
    CrewObservabilityAdapter,
    HookLoader,
    HookRegistry,
)

WORKSPACE_DIR = _M5L30_DIR / "workspace" / "demo_agent"
SKILLS_DIR = WORKSPACE_DIR / "skills"
OUTPUT_DIR = WORKSPACE_DIR / "output"

SANDBOX_MCP_URL = "http://localhost:8030/mcp"
SANDBOX_MOUNT_DESC = (
    "1. 所有操作必须在沙盒中执行，不得操作本地文件系统。\n"
    "   已挂载目录：\n"
    "   - skills → /mnt/skills:ro（Skill 资源，只读）\n"
    "   - output → /workspace/output:rw（产出物，可读写）\n\n"
    "2. 产出文件必须写到 /workspace/output/ 目录下\n"
    "3. 如遇依赖缺失，先在沙盒中安装再继续"
)

DEFAULT_TASK = "为一个用户注册功能产出技术设计文档"


def main():
    # 从命令行参数获取任务描述，如果没有则使用默认任务
    task_desc = " ".join(sys.argv[1:]).strip() or DEFAULT_TASK
    # 生成唯一的会话ID，使用当前UTC时间
    session_id = f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # ── 1. Hook 框架初始化 ──────────────────────────────────────────────────
    # 创建Hook注册表实例
    registry = HookRegistry()
    # 创建Hook加载器实例，并关联注册表
    loader = HookLoader(registry)
    # 从全局目录和工作空间目录加载两层Hook
    loader.load_two_layers(
        global_dir=_M5L30_DIR / "shared_hooks",
        workspace_dir=WORKSPACE_DIR,
    )

    # 获取并打印Hook摘要信息
    summary = registry.summary()
    total = sum(len(v) for v in summary.values())
    print(f"🔗 Session: {session_id}")
    print(f"📦 HookRegistry: {total} handlers loaded")
    # 打印每个事件及其对应的处理器
    for event, handlers in summary.items():
        for h in handlers:
            print(f"   {h} → {event}")
    print()

    # ── 2. CrewAI 适配层 ───────────────────────────────────────────────────
    # 创建CrewAI适配器实例，并关联注册表和会话ID
    adapter = CrewObservabilityAdapter(registry, session_id=session_id)
    # 安装全局Hook
    adapter.install_global_hooks()
    # 注册退出时的清理函数
    atexit.register(adapter.cleanup)

    # ── 3. Bootstrap + SkillLoader ─────────────────────────────────────────
    # 构建引导提示词
    backstory = build_bootstrap_prompt(WORKSPACE_DIR)

    # 创建技能加载工具实例
    skill_tool = SkillLoaderTool(
        skills_dir=str(SKILLS_DIR),
        sandbox_mcp_url=SANDBOX_MCP_URL,
        sandbox_mount_desc=SANDBOX_MOUNT_DESC,
    )

    # 💡 使用 llm.create_llm 创建 LLM，确保使用 llm_config 的配置
    # llm_config 会从环境变量 QWEN_API_KEY 中读取 API key
    from llm import create_llm
    model_name = os.environ.get("AGENT_MODEL", "qwen-turbo-1101")

    # 使用 create_llm 创建 LLM，它会自动从 llm_config 获取正确的 API key 和 base_url
    llm = create_llm(model=model_name)

    # 创建代理实例
    agent = Agent(
        role="数字员工",
        goal="根据用户请求，调用合适的 Skill 高效完成任务",
        backstory=backstory,
        llm=llm,
        verbose=True,
        tools=[skill_tool],
    )

    task = Task(
        description=(
            f"用户请求：{task_desc}\n\n"
            "请先调用 skill_loader 工具加载合适的 Skill 获取工作指引，"
            "然后严格按照指引完成任务。"
        ),
        expected_output="按照 Skill 指引产出的完整交付物",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
        step_callback=adapter.make_step_callback(),
        task_callback=adapter.make_task_callback(),
    )

    # ── 4. 执行 ────────────────────────────────────────────────────────────
    print(f"🚀 Task: {task_desc}\n")
    print(f"📋 Bootstrap: {len(backstory)} chars from workspace/demo_agent/")
    print(f"🔧 Skills: {list(skill_tool._skill_registry.keys())}\n")
    result = crew.kickoff()

    # ── 5. 清理 ────────────────────────────────────────────────────────────
    adapter.cleanup()

    print(f"\n{'='*60}")
    print(f"📊 Result:\n{result}")
    print(f"\n🔗 Langfuse: http://localhost:3000")
    design_doc = OUTPUT_DIR / "design_doc.md"
    if design_doc.exists():
        print(f"📄 Design doc: {design_doc}")
    audit_file = WORKSPACE_DIR / "audit.log"
    if audit_file.exists():
        print(f"📝 Audit log: {audit_file}")


if __name__ == "__main__":
    main()