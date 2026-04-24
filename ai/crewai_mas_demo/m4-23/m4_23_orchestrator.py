"""
第23课·Orchestrator范式：任务层的主 Agent + 子 Agent

核心演示：
  - 主 Agent 读取 SOP skill，根据需求自主决定何时/何种子 Agent
  - spawn_sub_agent：动态创建单个子 Agent（role/task/context 运行时决定）
  - spawn_sub_agents_parallel：并发启动多个独立子 Agent
  - 文件引用传递：结果写文件，传路径而非内容
  - reject + retry：主 Agent 验收不通过时重新 spawn 修复子 Agent

运行方式：
  cd m4l23 && python3 m4l23_orchestrator.py
"""


from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Type

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from crewai_tools import FileReadTool
from crewai_tools.tools.file_writer_tool.file_writer_tool import strtobool
from pydantic import BaseModel, Field

# ── 路径与项目根 sys.path（必须在 llm 模块 import 之前）──────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent                 # crewai_mas_demo 根目录
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from llm.unified_llm import create_llm_for_role
from llm.aliyun_llm import AliyunLLM

#llm = create_llm_for_role("assistant")    # 助手

# ── 常量 ──────────────────────────────────────────────────────────────────────
WORKSPACE_DIR    = _HERE / "workspace"
SKILL_PATH       = _PROJECT_ROOT / "skills" / "software-dev-sop" / "SKILL.md"
REQUIREMENTS_FILE = WORKSPACE_DIR / "requirements.md"


# ─────────────────────────────────────────────────────────────────────────────
# LLM 工厂
# - 主 Orchestrator 与所有子 Agent：qwen3.6-max-preview
# ─────────────────────────────────────────────────────────────────────────────

def _llm(model: str = "qwen3.6-max-preview") -> AliyunLLM:
    return create_llm_for_role("assistant")    # 助手


def _llm_for_sub_agent(role: str) -> AliyunLLM:
    """所有子 Agent 统一使用 qwen3.6-max-preview。"""
    return create_llm_for_role("lightweight")    # 轻量级的



# ─────────────────────────────────────────────────────────────────────────────
# BashTool（crewai_tools 未内置，手动实现）
# ─────────────────────────────────────────────────────────────────────────────

class _BashInput(BaseModel):
    command: str = Field(description="需要执行的 Shell 命令")



class BashTool(BaseTool):
    name: str = "BashTool"
    description: str = (
        "在 workspace 目录下执行 Shell 命令（cwd 已是本课 workspace 根目录），返回 stdout + stderr。"
        "适用于：运行 pytest、查看目录结构、执行 curl 等。"
        "⚠️ 路径规则："
        "1. 只使用相对路径，如：design/、tests/、backend/（不要用绝对路径）"
        "2. 禁止使用绝对路径（如 /home/...）"
        "3. 禁止使用 Users/...、workspace/... 等（会创建错误的嵌套目录）"
        "4. 创建目录时直接用目录名，如：mkdir -p design/api"
    )
    args_schema: Type[BaseModel] = _BashInput

    def _run(self, command: str) -> str:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR),
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        return output or "(no output)"

# ─────────────────────────────────────────────────────────────────────────────
# 路径解析：统一修正 LLM 常见误写
# 1) Users/xiao/... 无 leading / → 被 shell/cwd 当成相对路径 → workspace/Users/xiao/...
# 2) directory 写成 workspace/design（本课 cwd 已是 workspace）→ 误生成 workspace/workspace/design
# 3) 绝对路径里已出现 .../workspace/workspace/... → 折叠一层
# ─────────────────────────────────────────────────────────────────────────────

def _collapse_double_workspace_segment(p: Path) -> Path:
    """若路径中出现 .../workspace/workspace/...，折叠为 .../workspace/...。"""
    s = str(p.resolve())
    ws = str(WORKSPACE_DIR.resolve())
    double = ws + "/workspace"
    if s.startswith(double):
        remainder = s[len(double) :].lstrip("/")
        return Path(ws) / remainder if remainder else Path(ws)
    return p

def _resolve_workspace_path(path_str: str) -> Path:
    """将 LLM 给出的单一路径段解析为绝对路径（用于目录或单文件）。"""
    raw = str(path_str).strip().replace("\\", "/")
    if not raw:
        return WORKSPACE_DIR
    while raw.startswith("./"):
        raw = raw[2:]
    p = Path(raw)
    if p.is_absolute():
        rp = p.resolve()
        ws_resolved = WORKSPACE_DIR.resolve()

        # 如果绝对路径直接在 workspace 下，直接使用
        try:
            rel_to_workspace = rp.relative_to(ws_resolved)
            return rp  # 已经在 workspace 下，直接返回
        except ValueError:
            pass

        # 如果绝对路径在 m4-23 目录下但不在 workspace 下，转换到 workspace
        # 例如：/home/.../m4-23/design -> /home/.../m4-23/workspace/design
        try:
            # 尝试找到项目根目录（m4-23 的父目录）
            project_parts = ws_resolved.parts  # [..., "crewai_mas_demo", "m4-23", "workspace"]
            if 'workspace' in project_parts:
                workspace_idx = project_parts.index('workspace')
                # 项目根目录到 m4-23
                project_root_parts = project_parts[:workspace_idx]  # [..., "crewai_mas_demo", "m4-23"]
                project_root = Path(*project_root_parts)

                # 检查绝对路径是否在项目下
                try:
                    rel_to_project = rp.relative_to(project_root)
                    rel_parts = list(rel_to_project.parts)

                    # 如果路径以 "m4-23" 开头，去掉它
                    if rel_parts and rel_parts[0] == 'm4-23':
                        rel_parts = rel_parts[1:]

                    # 如果路径包含 "workspace"，去掉它及之前的部分
                    if 'workspace' in rel_parts:
                        ws_idx = rel_parts.index('workspace')
                        rel_parts = rel_parts[ws_idx + 1:]

                    # 转换到 workspace 下
                    if rel_parts:
                        return ws_resolved / Path(*rel_parts)
                    else:
                        return ws_resolved
                except ValueError:
                    pass
        except Exception:
            pass

        # 其他情况，使用原路径但折叠重复的 workspace
        return _collapse_double_workspace_segment(rp)

    if raw.lower().startswith("users/"):
        return _collapse_double_workspace_segment((Path("/") / raw).resolve())
    # 已处在 workspace 目录下却又写了 workspace/xxx
    if raw == "workspace" or raw.startswith("workspace/"):
        rest = raw[len("workspace") :].lstrip("/") or "."
        return _collapse_double_workspace_segment((WORKSPACE_DIR / rest).resolve())
    return _collapse_double_workspace_segment((WORKSPACE_DIR / raw).resolve())


def _resolve_workspace_filepath(directory: str | None, filename: str) -> Path:
    """组合 directory + filename，并消除重复 workspace 段。"""
    fn = str(filename).strip().replace("\\", "/")
    if not fn:
        return _resolve_workspace_path(directory or ".")
    if Path(fn).is_absolute():
        return _resolve_workspace_path(fn)
    while fn.startswith("./"):
        fn = fn[2:]
    if fn == "workspace" or fn.startswith("workspace/"):
        fn = fn[len("workspace") :].lstrip("/")
    base = _resolve_workspace_path(directory or ".")
    return _collapse_double_workspace_segment((base / fn).resolve())

# ─────────────────────────────────────────────────────────────────────────────
# WorkspaceFileWriterTool / WorkspaceFileReadTool
# ─────────────────────────────────────────────────────────────────────────────
class _WorkspaceWriterInput(BaseModel):
    filename: str = Field(description="文件名，可含子目录片段")
    directory: str | None = Field(
        default="./",
        description=(
            "目标目录：绝对路径，或相对本课 workspace 根的路径（如 design/、frontend/）。"
            "不要写 workspace/design（cwd 已是 workspace，会叠成 workspace/workspace）。"
            "不要写无 / 开头的 Users/... 。"
        ),
    )
    overwrite: str | bool = False
    content: str = Field(description="文件全文")

class WorkspaceFileWriterTool(BaseTool):
    """
    文件写入工具类，用于将内容写入指定目录下的文件。
    继承自BaseTool基类，提供了文件写入的基本功能。
    """
    name: str = "File Writer Tool"
    description: str = (
        "将内容写入指定目录下的文件。"
        "⚠️ 路径规则："
        "1. directory 参数：只用相对路径，如 design、mock、tests（不要用绝对路径，不要用 /home/...）"
        "2. filename 参数：文件名，可含子目录，如 api/spec.yaml（不要加 / 前缀）"
        "3. 禁止使用：workspace/design、/home/...、Users/... 等（会创建错误的嵌套目录）"
        "4. 正确示例：directory='design', filename='architecture.md'"
        "5. 正确示例：directory='mock', filename='server/main.py'"
    )
    args_schema: Type[BaseModel] = _WorkspaceWriterInput

    def _run(
        self,
        filename: str,  # 文件名参数，必须是字符串类型
        directory: str | None = "./",  # 目录参数，可选，默认为当前目录"./"
        overwrite: str | bool = False,  # 覆盖参数，可以是字符串或布尔值，默认为False
        content: str = "",  # 要写入的内容参数，必须是字符串类型，默认为空字符串
    ) -> str:  # 返回值类型为字符串
        try:
            # 解析工作区文件路径，将目录和文件名组合成完整路径
            filepath = _resolve_workspace_filepath(directory, filename)
            # 创建必要的父目录，如果已存在则不创建
            filepath.parent.mkdir(parents=True, exist_ok=True)
            # 将overwrite参数转换为布尔值，如果已经是布尔值则直接使用
            overwrite_b = strtobool(overwrite) if not isinstance(overwrite, bool) else overwrite
            # 检查文件是否已存在且不允许覆盖
            if filepath.exists() and not overwrite_b:
                return f"File {filepath} already exists and overwrite option was not passed."
            # 根据是否覆盖决定文件打开模式
            mode = "w" if overwrite_b else "x"
            # 以UTF-8编码打开文件并写入内容
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(content)
            # 返回成功写入的消息
            return f"Content successfully written to {filepath}"
        except FileExistsError:
            # 处理文件已存在的情况
            return f"File {filepath} already exists and overwrite option was not passed."
        except Exception as e:
            # 处理其他可能的异常
            return f"An error occurred while writing to the file: {e!s}"

class WorkspaceFileReadTool(FileReadTool):
    """读文件前做与 Writer 一致的路径解析，避免 workspace/workspace 与 Users/ 误路径。"""

    def _run(
        self,
        file_path: str | None = None,  # 文件路径参数，可以是字符串或None
        start_line: int | None = 1,     # 起始行号参数，默认为1
        line_count: int | None = None,  # 行数参数，可以是None表示全部行
    ) -> str:                         # 返回类型为字符串
        # 如果没有提供文件路径，则使用类实例中的file_path属性
        fp = file_path or self.file_path
        # 如果文件路径为None，返回错误信息
        if fp is None:
            return "Error: No file path provided. Please provide a file path either in the constructor or as an argument."
        # 解析工作区路径并转换为字符串
        resolved = str(_resolve_workspace_path(fp))
        # 调用父类的_run方法，传入解析后的路径和其他参数
        return super()._run(
            file_path=resolved, start_line=start_line, line_count=line_count
        )

# ─────────────────────────────────────────────────────────────────────────────
# TOOL_REGISTRY：预定义工具池
# 工具池在代码中预定义；哪个子 Agent 用哪些，由主 Agent 在 spawn 时传 tool_names 决定
# ─────────────────────────────────────────────────────────────────────────────
TOOL_REGISTRY: dict[str, Any] = {
    "FileReadTool":   WorkspaceFileReadTool(),
    "FileWriterTool": WorkspaceFileWriterTool(),
    "BashTool":       BashTool(),
}

# ─────────────────────────────────────────────────────────────────────────────
# 核心：动态 sub-crew 运行器
# 每次调用都实例化全新的 Agent / Task / Crew，不共享任何状态（上下文隔离）
# ─────────────────────────────────────────────────────────────────────────────
def _run_one_sub_crew(
    role: str,
    goal: str,
    task: str,
    context: str,
    tool_names: str,
    output_file: str,
) -> str:
    """
    动态实例化一个独立 sub-crew 并运行。

    role / goal / task / context 全部由调用方（主 Agent）在运行时决定，
    这里没有任何预定义的角色类——这是 Orchestrator 范式和工作流的核心区别。
    """
    # 从工具池中按名称取工具，未知名称静默跳过
    tools = [
        TOOL_REGISTRY[t.strip()]
        for t in tool_names.split(",")
        if t.strip() in TOOL_REGISTRY
    ]

    # 确保输出目录存在
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = WORKSPACE_DIR / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    agent = Agent(
        role=role,
        goal=goal,
        backstory=context,
        tools=tools,
        llm=_llm_for_sub_agent(role),
        verbose=True,
    )
    task_obj = Task(
        description=task,
        expected_output=f"将结果写入 {output_path}，返回该文件的绝对路径字符串",
        agent=agent,
        output_file=str(output_path),
    )
    Crew(agents=[agent], tasks=[task_obj], verbose=True).kickoff()
    return str(output_path)

# ─────────────────────────────────────────────────────────────────────────────
# spawn_sub_agent Tool
# ─────────────────────────────────────────────────────────────────────────────

class _SpawnSingleInput(BaseModel):
    role: str = Field(description="子 Agent 的角色名（你在运行时决定，如 'Frontend Developer'）")
    goal: str = Field(description="子 Agent 的目标（一句话）")
    task: str = Field(description="详细任务描述，包含所有子 Agent 需要知道的信息")
    context: str = Field(
        description="子 Agent 需要的完整上下文（显式传入，不依赖隐式共享）"
    )
    tool_names: str = Field(
        description="逗号分隔的工具名，可选：FileReadTool, FileWriterTool, BashTool"
    )
    output_file: str = Field(
        description="结果写入的文件路径（相对 workspace/ 或绝对路径）"
    )

class SpawnSubAgentTool(BaseTool):
    name: str = "spawn_sub_agent"
    description: str = (
        "动态创建并运行一个子 Agent（串行，等待完成后返回）。"
        "role / goal / task / context 由你在运行时决定，没有预定义的角色限制。"
        "子 Agent 在完全独立的上下文中运行（不知道你做过什么），"
        "完成后将结果写入 output_file，返回文件路径。"
        "适用于：需要串行执行的单个子任务，或与其他任务有依赖关系的任务。"
    )
    args_schema: Type[BaseModel] = _SpawnSingleInput

    def _run(
        self,
        role: str,          # 角色名称，用于标识子代理的身份
        goal: str,          # 子代理的目标，指导其行为方向
        task: str,          # 子代理需要执行的具体任务
        context: str,       # 上下文信息，提供任务执行的环境背景
        tool_names: str,    # 可用工具的名称列表，以字符串形式提供
        output_file: str,   # 输出文件的路径，用于保存任务执行结果
    ) -> str:             # 返回类型注解，表明该方法返回一个字符串类型的结果
        print(f"\n[sub-agent: {role}] 启动 (独立上下文)")  # 打印子代理启动信息，包含角色名称
        result = _run_one_sub_crew(  # 调用_run_one_sub_crew函数执行子代理任务
            role=role,
            goal=goal,          # 传入目标
            task=task,          # 传入任务
            context=context,    # 传入上下文
            tool_names=tool_names,  # 传入工具名称列表
            output_file=output_file,  # 传入输出文件路径
        )
        print(f"[sub-agent: {role}] 完成 → {result}")  # 打印子代理完成信息，包含角色名称和执行结果
        return result  # 返回执行结果
    
# ─────────────────────────────────────────────────────────────────────────────
# spawn_sub_agents_parallel Tool
# ─────────────────────────────────────────────────────────────────────────────
class _SpawnParallelInput(BaseModel):
    subtasks_json: str = Field(
        description=(
            "JSON 数组，每项格式与 spawn_sub_agent 参数相同："
            "[{role, goal, task, context, tool_names, output_file}, ...]。"
            "你决定数组中放什么、放多少个。"
            "前提：各任务的输入不依赖对方输出，且输出目录不重叠。"
        )
    )


class SpawnParallelTool(BaseTool):

    """
    并发启动多个互相独立的子 Agent 的工具类。
    所有任务同时运行，适用于多个任务互相独立、没有先后依赖、可以并发执行的场景。
    """
    name: str = "spawn_sub_agents_parallel"  # 工具名称
    description: str = (
        "并发启动多个互相独立的子 Agent（所有任务同时运行）。"
        "输入：JSON 数组，每项与 spawn_sub_agent 参数相同。"
        "全部完成后返回结果 JSON：{output_file: 'done' | 'error: ...'} 。"
        "适用于：多个任务互相独立、没有先后依赖、可以并发执行的场景。"
        "注意：并发任务不能写同一个文件（会冲突）。"
    )
    args_schema: Type[BaseModel] = _SpawnParallelInput  # 参数模式定义

    def _run(self, subtasks_json: str) -> str:
        subtasks: list[dict] = json.loads(subtasks_json)
        results: dict[str, str] = {}

        print(f"\n[并发启动] {len(subtasks)} 个子 Agent 同时运行...")
        for st in subtasks:
            print(f"  [{st['role']}] 启动 (独立上下文)")

        with ThreadPoolExecutor(max_workers=len(subtasks)) as executor:
            futures = {
                executor.submit(
                    _run_one_sub_crew,
                    role=st["role"],
                    goal=st["goal"],
                    task=st["task"],
                    context=st["context"],
                    tool_names=st["tool_names"],
                    output_file=st["output_file"],
                ): st["output_file"]
                for st in subtasks
            }
            for future in as_completed(futures):
                output_file = futures[future]
                try:
                    results[output_file] = future.result()
                    print(f"  [完成] → {output_file}")
                except Exception as e:
                    results[output_file] = f"error: {e}"
                    print(f"  [失败] {output_file}: {e}")

        return json.dumps(results, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# SOP Skill 加载
# ─────────────────────────────────────────────────────────────────────────────
def load_sop_skill() -> str:
    """读取 software-dev-sop SKILL.md，注入到主 Agent backstory"""
    if SKILL_PATH.exists():
        return SKILL_PATH.read_text(encoding="utf-8")
    return f"(SOP skill 未找到，期望路径：{SKILL_PATH})"

# ─────────────────────────────────────────────────────────────────────────────
# 主 Agent（Orchestrator）
# ─────────────────────────────────────────────────────────────────────────────

def build_orchestrator() -> tuple[Agent, Task]:
    # 加载SOP（标准操作流程）技能内容
    sop_content = load_sop_skill()

    # 创建编排器Agent，负责协调整个软件开发流程
    orchestrator = Agent(
        # 定义Agent的角色和目标
        role="Software Development Orchestrator",
        goal=(
            "接收软件需求文档，按 SOP **一次性连续跑完**各阶段，协调子 Agent 完成设计、实现、测试与交付；"
            "不中断、不向用户提问；遇失败时**先分析再派单**，避免无差别重复 spawn。"
            "你只做拆解、派单、验收与策略性重试，不执笔任何文档或代码。"
        ),
        # 定义Agent的背景故事和工作方式
        backstory=(
            "你是一名有 10 年全栈经验的技术负责人，擅长把模糊需求拆解成清晰可执行的子任务。\n"
            "你的工作方式：\n"
            "1. 架构/接口/代码/报告一律由子 Agent 产出——你只读需求、spawn、用 FileReadTool 验收\n"
            "2. 给子 Agent 派任务时，总是显式传递它需要的全部信息，"
            "绝不假设它能'感知'你做过什么\n"
            "3. 独立的任务用并发子 Agent；有依赖关系的严格串行\n"
            "4. 始终按照下方 SOP 流程推进，不跳过任何阶段\n"
            "5. **一次跑完全程**：不向用户提问或求确认；遇阻按 SOP「失败处理」分析后再 spawn\n"
            "6. **失败时禁止无脑重试**：读完 review/test 报告后，先自行分类（环境/导入/测试写法/业务逻辑），"
            "写出简短根因假设与「下一步验证或修改建议」，再 spawn Debugger/QA；"
            "同一失败模式若已重试仍相同，必须**换策略**（换任务描述、补充上下文、收窄范围），"
            "不得原样复制上一轮的 spawn 参数\n\n"
            "你的工具：\n"
            "- spawn_sub_agent：开一个子 Agent 执行单个任务（串行）\n"
            "- spawn_sub_agents_parallel：同时开多个互相独立的子 Agent（并发）\n"
            "- FileReadTool：读取文件内容（读需求文档、验收子 Agent 输出）\n\n"
            "━━━ SOP 流程（必须遵守）━━━\n\n"
            f"{sop_content}"
        ),
        # 配置Agent可用的工具
        tools=[SpawnSubAgentTool(), SpawnParallelTool(), FileReadTool()],
        # 配置Agent使用的语言模型
        llm=_llm("qwen3.6-max-preview"),
        verbose=True,
    )

    # 创建主任务，定义整个软件开发流程的执行步骤
    main_task = Task(
        description=(
            f"读取需求文档 {REQUIREMENTS_FILE}，按照 SOP 完成完整交付（你只协调，不执笔）：\n\n"
            "1. 阶段 1：spawn 子 Agent 产出 A（architecture.md）与 B（api_spec.md），你用 FileReadTool 分别验收\n"
            "2. 阶段 2～5：按 SOP 协调子 Agent：mock/单测 → 前后端开发 → 代码审查+测试 → 修复循环\n"
            "3. 阶段 6：spawn 子 Agent 写 workspace/delivery_report.md（仅路径引用，不复制代码），你再读取确认\n\n"
            "关键约束：\n"
            "- **一次性做完整个 SOP**，中间不要停、不要向用户提问或等待确认；有问题按 SOP 自己解决\n"
            "- **验收或测试失败后**：先读报告与相关文件，做根因分类并写出「解决建议」再 spawn；"
            "禁止用与上一轮完全相同的 task/context 重复 spawn Debugger/QA\n"
            "- spawn 子 Agent 时必须显式传递完整上下文（文件内容，不只是路径）；"
            "修复类 spawn 须在 context 中包含：失败摘要、你的分析、建议子 Agent 采取的具体步骤\n"
            f"- 所有产出文件放在 {WORKSPACE_DIR}/ 下\n"
            "- 子 Agent 完成后必须用 FileReadTool 读取输出文件确认内容\n"
        ),
        # 定义任务的预期输出
        expected_output=(
            "workspace/delivery_report.md 的绝对路径，"
            "文件存在且包含各模块文件路径引用"
        ),
        # 指定执行该任务的Agent
        agent=orchestrator,
        # 定义输出文件的路径
        output_file=str(WORKSPACE_DIR / "delivery_report.md"),
    )

    # 返回编排器Agent和主任务
    return orchestrator, main_task


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

def run() -> Any:
    # 避免 CrewAI 首次运行后弹出「是否查看 execution traces」阻塞或打断自动化流程
    os.environ.setdefault("CREWAI_TESTING", "true")

    print("=" * 60)
    print("第23课·Orchestrator范式 演示")
    print(f"需求文档 : {REQUIREMENTS_FILE}")
    print(f"SOP Skill: {SKILL_PATH}")
    print("=" * 60)

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    if not REQUIREMENTS_FILE.exists():
        print(f"\n[错误] 需求文档不存在: {REQUIREMENTS_FILE}")
        print("请先创建 workspace/requirements.md")
        return None

    orchestrator, main_task = build_orchestrator()
    crew = Crew(
        agents=[orchestrator],
        tasks=[main_task],
        verbose=True,
    )
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("✅ 完成。交付报告: workspace/delivery_report.md")
    print("=" * 60)
    return result


if __name__ == "__main__":
    run()