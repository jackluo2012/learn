"""
通用数字员工框架 — 所有角色共用同一个类，零角色特异性代码。

核心原则（第25课）：静态的框架，动态的 Workspace
  - role/goal 使用通用值，角色身份完全由 workspace 文件决定
  - Task 使用通用模板，具体行为由 agent.md 和 Skill 驱动
  - 代码层面不包含任何角色特异性内容

复用关系：
  - build_bootstrap_prompt：直接复用 m3l20，zero change
  - SkillLoaderTool：直接复用，传入 workspace 对应的沙盒参数
  - prune_tool_results / maybe_compress：直接复用
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from crewai import Agent, Crew, Task
from crewai.hooks import LLMCallHookContext, before_llm_call
from crewai.project import CrewBase, agent, crew, llm, task

from llm.unified_llm import create_llm_for_role


_SHARED_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SHARED_DIR.parent
for _p in [str(_SHARED_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm.aliyun_llm import AliyunLLM  # noqa: E402
from tools.skill_loader_tool import SkillLoaderTool  # noqa: E402

from m3_20.m3_20_file_memory import (  # noqa: E402
    build_bootstrap_prompt,
    load_session_ctx,
    save_session_ctx,
    append_session_raw,
    prune_tool_results,
    maybe_compress,
)

UNIVERSAL_ROLE = "数字员工"
UNIVERSAL_GOAL = "根据你的背景信息和可用技能，完成收到的任务"

UNIVERSAL_TASK_TEMPLATE = """\
你收到了以下任务请求：

{user_request}

请根据你的角色背景（<soul> 中的身份和决策偏好）、\
职责边界（<agent_rules> 中的职责和规范）、\
可用技能（通过 skill_loader 加载）、\
以及记忆（<memory_index> 中的历史信息），\
来完成这个任务。

你需要：
1. 先理解自己是谁、该做什么
2. 加载相关的 Skill 来获取具体的操作方法
3. 按照 Skill 中的指引自主完成任务
4. 将结果输出到适当的位置
"""

UNIVERSAL_EXPECTED_OUTPUT = "根据你的角色职责和任务要求，产出对应的交付物"


def build_sandbox_mount_desc(
    workspace_label: str = "workspace",
    has_shared: bool = False,
) -> str:
    """根据 workspace 配置生成沙盒挂载描述。

    沙盒挂载两路：
      - workspace 目录 → /workspace:rw（输出文件写入此处）
      - 全局 skills 目录 → /mnt/skills:ro（memory-save 等任务型脚本从此读取）
    """
    lines = [
        "1. 所有的操作必须在沙盒中执行，不得操作本地文件系统。",
        "   当前已挂载的目录：",
        f"   - ./{workspace_label}:/workspace:rw（角色 workspace，可读写）",
    ]
    if has_shared:
        lines.append(
            "   - ./workspace/shared:/mnt/shared:rw（共享工作区，可读写）"  # shared 路径固定
        )
    lines.extend([
        "   - ../skills:/mnt/skills:ro（全局 skills，任务型脚本从此读取）",
        "",
        "2. 文件操作规范：",
        "   - 读写用沙盒绝对路径，如 /workspace/xxx.md",
        "   - 共享文件用 /mnt/shared/ 路径",
        "",
        "3. 参考型 Skill（type: reference）：内容直接注入上下文，无需沙盒执行",
        "",
        "4. 如遇依赖缺失，先在沙盒中安装再继续",
    ])
    return "\n".join(lines)


@CrewBase
class DigitalWorkerCrew:
    """
    通用数字员工 — 所有角色共用同一个类。

    角色身份由 workspace 目录下的四个文件决定：
      soul.md   → 注入到 <soul> 标签（身份、决策偏好、NEVER 清单）
      agent.md  → 注入到 <agent_rules> 标签（职责边界、工作规范、交付物格式）
      user.md   → 注入到 <user_profile> 标签（服务对象画像）
      memory.md → 注入到 <memory_index> 标签（跨 session 记忆索引）

    代码层面不包含任何角色特异性内容。
    """

    def __init__(
        self,
        workspace_dir: str | Path,
        sandbox_port: int,
        session_id: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        has_shared: bool = False,
        max_iter: int = 25,
        llmrole:str= "assistant",
    ) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.sandbox_port = sandbox_port
        self.session_id = session_id or f"session_{uuid4().hex[:8]}"
        self.model = model or os.getenv("DIGITAL_WORKER_MODEL", "qwen-max-latest")
        self.temperature = temperature
        self.has_shared = has_shared
        self.max_iter = max_iter
        self.llmrole = llmrole

        self.sessions_dir = self.workspace_dir / "sessions"
        self._session_loaded = False
        self._last_msgs: list[dict] = []
        self._history_len = 0

        workspace_label = f"workspace/{self.workspace_dir.name}"
        self._sandbox_mount_desc = build_sandbox_mount_desc(
            workspace_label=workspace_label,
            has_shared=has_shared,
        )

    @agent
    def worker_agent(self) -> Agent:
        backstory = build_bootstrap_prompt(self.workspace_dir)
        # 💡 v3 核心：workspace-local skills 目录优先加载
        # Agent 的能力完全由 workspace 决定，换 workspace 即换能力
        workspace_skills = self.workspace_dir / "skills"
        # 直接用 AliyunLLM，完全去掉 openai provider 依赖
        llm = AliyunLLM(
            model=self.model if self.model else None,
            temperature=self.temperature,
        )
        return Agent(
            role=UNIVERSAL_ROLE,
            goal=UNIVERSAL_GOAL,
            backstory=backstory,
            llm=llm,
            tools=[
                SkillLoaderTool(
                    sandbox_mount_desc=self._sandbox_mount_desc,
                    sandbox_mcp_url=f"http://localhost:{self.sandbox_port}/mcp",
                    skills_dir=str(workspace_skills) if workspace_skills.is_dir() else "",
                ),
            ],
            verbose=True,
            max_iter=self.max_iter,
        )

    @task
    def worker_task(self) -> Task:
        return Task(
            description=UNIVERSAL_TASK_TEMPLATE,
            expected_output=UNIVERSAL_EXPECTED_OUTPUT,
            agent=self.worker_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

    @before_llm_call
    def before_llm_hook(self, context: LLMCallHookContext) -> bool | None:
        if not self._session_loaded:
            self._restore_session(context)
            self._session_loaded = True
        self._last_msgs = context.messages
        prune_tool_results(context.messages)
        maybe_compress(context.messages, context)
        return None

    def _restore_session(self, context: LLMCallHookContext) -> None:
        history = load_session_ctx(self.session_id, self.sessions_dir)
        self._history_len = len(history)
        if not history:
            return
        current_user_msg = next(
            (m for m in reversed(context.messages) if m.get("role") == "user"),
            {},
        )
        context.messages.clear()
        context.messages.extend(history)
        if current_user_msg:
            context.messages.append(current_user_msg)

    def kickoff(self, user_request: str) -> str:
        """启动数字员工执行任务，返回结果文本。"""
        crew_instance = self.crew()
        result = crew_instance.kickoff(
            inputs={"user_request": user_request}
        )

        if self._last_msgs:
            new_msgs = list(self._last_msgs)[self._history_len:]
            append_session_raw(self.session_id, new_msgs, self.sessions_dir)
            save_session_ctx(
                self.session_id, list(self._last_msgs), self.sessions_dir
            )

        return result.raw