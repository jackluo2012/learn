"""
课程：16｜Skills 生态：让 Agent 接入大量工具
核心组件：SkillLoaderTool

设计要点：
  1. 渐进式披露（Progressive Disclosure）
     - __init__ 只解析 SKILL.md 的 YAML frontmatter，构建轻量 XML 注入工具 description
     - 主 Agent 通过 description 感知"有哪些 Skill、各自用途"
     - 真正调用时才读取完整 SKILL.md 正文（按需加载）

  2. 参考型 vs 任务型
     - reference：返回指令文本，主 Agent 自行消化，不启动 Sub-Crew
     - task：触发独立 Sub-Crew + AIO-Sandbox 执行，上下文完全隔离

  3. 异步双通道
     - _arun()：FastAPI akickoff() 调用链的主路径，原生 await
     - _run()：同步 fallback，ThreadPoolExecutor 提供独立 event loop，
               规避 "cannot run nested event loop" 错误
"""

import asyncio
import concurrent.futures
import json
import re
import sys
from pathlib import Path
from typing import Any, Union

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.mcp import MCPServerHTTP
from crewai.mcp.filters import create_static_tool_filter
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr, field_validator

# 将项目根（crewai_mas_demo/）加入 sys.path，使 llm 包可被 import
_TOOLS_DIR = Path(__file__).parent
_PROJECT_ROOT = _TOOLS_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from llm import AliyunLLM  # noqa: E402

# ── 路径常量 ────────────────────────────────────────────────────────────────
# SKILLS_DIR：共享 skills 目录（crewai_mas_demo/skills/），所有课程共用
# 💡 核心点：__file__ 是 tools/skill_loader_tool.py，上一层是 tools/，上两层即 crewai_mas_demo/
SKILLS_DIR = _PROJECT_ROOT / "skills"

# 沙盒内的 skills 挂载路径（与 sandbox-docker-compose.yaml 的 volumes 对应）
SANDBOX_SKILLS_MOUNT = "/mnt/skills"

# ── AIO-Sandbox MCP 配置（Sub-Crew 使用） ─────────────────────────────────────

# 需要提前通过 sandbox-docker-compose.yaml 启动 AIO-Sandbox，端口 8022 对应 8080
SANDBOX_MCP_URL = "http://localhost:8022/mcp"

# 白名单过滤：只开放 4 个沙盒工具，排除 browser_* 系列
SANDBOX_TOOL_FILTER = create_static_tool_filter(
    allowed_tool_names=[
        "sandbox_execute_bash",
        "sandbox_execute_code",
        "sandbox_file_operations",
        "sandbox_str_replace_editor",
    ]
)

# 💡 核心点：默认沙盒挂载描述（m2l16 原始行为）
# 抽成常量后，可在实例化 SkillLoaderTool 时传入自定义值（见 m3l20）
DEFAULT_SANDBOX_MOUNT_DESC = (
    "1. 所有的操作必须在沙盒中执行，不得操作本地文件系统，当前已挂载在沙盒的本地目录为"
    "./workspace/data:/workspace/data:ro和./workspace/output:/workspace/output:rw\n"
    "2. 如果需要读取本地文件，则需要本地文件在./workspace/data/目录下，且提供的本地路径会在"
    "对应沙盒绝对路径的/workspace/data/目录下。如果文件不在./workspace/data/目录下，则需要"
    "提示用户本地文件路径错误，无法执行任务。\n"
    "3. 任务预期输出的文件，必须写在沙盒绝对路径的/workspace/output/目录下，且提供的本地路径"
    "会在对应的./workspace/output/目录下\n"
    "4. 如遇依赖缺失，先在沙盒中安装再继续"
)


def build_skill_crew(
    skill_name: str,
    skill_instructions: str,
    mount_desc: str = DEFAULT_SANDBOX_MOUNT_DESC,  # 💡 mount_desc 参数：默认保持 m2l16 行为，m3l20 传入新挂载描述
    mcp_url: str = SANDBOX_MCP_URL,  # 💡 mcp_url 参数：m4l25 Manager=8023, Dev=8024
) -> Crew:
    """
    Sub-Crew 工厂：为指定 Skill 构建一个在 AIO-Sandbox 中执行的 Crew。
    mount_desc 描述沙盒挂载路径，默认为 m2l16 的 data:ro + output:rw。
    传入自定义 mount_desc 可适配不同课程的沙盒配置，不影响其他参数。
    mcp_url 指定沙盒 MCP 端点，m4l25 Manager/Dev 各用独立端口。
    """
    sandbox_mcp = MCPServerHTTP(
        url=mcp_url,
        #tool_filter=SANDBOX_TOOL_FILTER, # 暂时不使用工具过滤，因为目前工具都用得上
    )

    skill_llm = AliyunLLM(model="qwen-max-latest", region="cn", temperature=0.3)

    skill_agent = Agent(
        role=f"{skill_name.upper()} Skill 执行专家",
        goal=f"严格按照 {skill_name} Skill 的操作规范，在 AIO-Sandbox 中完成任务",
        backstory=(
            f"你是一位专精于 {skill_name} 文件处理的 AI 专家。\n"
            f"你掌握以下操作规范，请严格遵循：\n\n"
            f"{skill_instructions}"
        ),
        llm=skill_llm,
        mcps=[sandbox_mcp],
        verbose=True,
        max_iter=10,
    )

    skill_task = Task(
        description=(
            "根据以下任务要求，使用你掌握的 Skill 操作规范完成任务。\n\n"
            "任务要求：\n{task_context}\n\n"
            "执行要求：\n"
            + mount_desc  # 💡 替换原硬编码挂载字符串，由调用方配置
        ),
        expected_output=(
            "一份结构化的任务执行结果，按照任务要求中的json schema输出。"
        ),
        agent=skill_agent,
    )

    return Crew(
        agents=[skill_agent],
        tasks=[skill_task],
        process=Process.sequential,
        verbose=True,
    )


# ── 输入 Schema ─────────────────────────────────────────────────────────────


class SkillLoaderInput(BaseModel):
    skill_name: str = Field(
        description="要加载的 Skill 名称，必须严格来自工具描述 XML 列表中的 <name> 值"
    )
    task_context: str = Field(
        default="",
        description=(
            "如果是参考型skill，此项为空。\n"
            "如果是任务型skill，此项为调用此 Skill 要完成的子任务的完整描述（必须是字符串）。"
            "可写自然语言描述，或 JSON 字符串。若传入对象会自动转为 JSON 字符串。包括：\n"
            "1. 子任务的概要描述\n"
            "2. 任务完成目标的预期输出，这里必须是结构化格式，通过一个json schema进行定义。各个字段的描述必须有明确的描述和示例.有两个必选字段errcode和errmsg，errcode为0表示成功，非0表示失败，errmsg为错误信息，成功时固定返回\"success\"，失败时必须包括错误信息、错误原因和建议的下一步解决方案。\n"
            "3. （可选）如果有完成任务的参考步骤和方法，可以提供对应描述\n"
            "4. （可选）如果完成任务有输入文件，则需要提供输入文件的沙盒绝对路径（如 /workspace/data/report.pdf），如果该文件是本地文件，沙盒路径是由本地文件系统挂载的，挂载配置: ./workspace/data:/workspace/data:ro，因此本地的文件路径需要转换为沙盒路径。如果该文件是沙盒内文件，则直接提供文件路径即可。\n"
            "5. （可选）如果完成任务有输出文件，则需要在json schema中定义输出文件的格式，并提供输出文件的本地路径,因为挂载配置:./workspace/output:/workspace/output:rw，所以要保证沙盒路径在/workspace/output/目录下, 且提供的本地路径会在对应的./workspace/output/目录下\n"
            "4. （可选）如果有其它特殊要求，可以在此处提供\n"
            "提供信息越完整，Skill 执行越精准。"
        ),
    )

    @field_validator("task_context", mode="before")
    @classmethod
    def task_context_to_str(cls, v: Union[str, dict, list, None]) -> str:
        """LLM 常传 dict/list，此处统一转为字符串，避免 Pydantic string_type 校验失败。"""
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)


# ── 核心工具 ─────────────────────────────────────────────────────────────────


class SkillLoaderTool(BaseTool):
    name: str = "skill_loader"
    description: str = ""  # 在 __init__ 中动态构建
    args_schema: type[BaseModel] = SkillLoaderInput

    # 💡 沙盒挂载描述：默认保持 m2l16 行为，传入自定义值适配不同课程
    # m2l16：SkillLoaderTool()  →  使用 data:ro + output:rw 挂载
    # m3l20：SkillLoaderTool(sandbox_mount_desc=M3L20_SANDBOX_MOUNT_DESC)  →  workspace:rw
    sandbox_mount_desc: str = DEFAULT_SANDBOX_MOUNT_DESC

    # 💡 沙盒 MCP URL：默认 8022，各课程可传入自定义端口（m4l25 Manager=8023, Dev=8024）
    sandbox_mcp_url: str = SANDBOX_MCP_URL

    # 💡 v3：workspace-local skills 目录（空字符串 = 使用全局 SKILLS_DIR，保持向后兼容）
    # m4l25 Manager：workspace/manager/skills/
    # m4l25 Dev：workspace/dev/skills/
    skills_dir: str = ""

    # Pydantic 会把普通 dict 属性当作模型字段，用 PrivateAttr 绕开
    _skill_registry: dict[str, Any] = PrivateAttr(default_factory=dict)
    _instruction_cache: dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(
        self,
        sandbox_mount_desc: str = DEFAULT_SANDBOX_MOUNT_DESC,
        sandbox_mcp_url: str = SANDBOX_MCP_URL,
        skills_dir: str = "",
    ):
        super().__init__(
            sandbox_mount_desc=sandbox_mount_desc,
            sandbox_mcp_url=sandbox_mcp_url,
            skills_dir=skills_dir,
        )
        # 实例级属性，避免类级共享
        self._skill_registry = {}
        self._instruction_cache = {}
        self._build_description()

    def _effective_skills_dir(self) -> Path:
        """返回 workspace-local skills 目录（若已配置），否则返回全局 SKILLS_DIR。"""
        if self.skills_dir:
            return Path(self.skills_dir)
        return SKILLS_DIR

    def _resolve_skill_path(self, skill_name: str) -> Path | None:
        """
        💡 核心点：双目录查找策略
        1. 优先在 workspace-local skills 目录查找
        2. 找不到时回退到全局 SKILLS_DIR
        这样 workspace 只需放角色独有的 Skill，通用 Skill（memory-save、write-output 等）
        不必在每个 workspace 中重复维护。
        """
        import logging
        workspace_dir = self._effective_skills_dir()
        skill_path = workspace_dir / skill_name
        if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
            return skill_path
        # 用 .resolve() 比较，避免符号链接 / 相对路径导致误判
        if workspace_dir.resolve() != SKILLS_DIR.resolve():
            global_path = SKILLS_DIR / skill_name
            if global_path.is_dir() and (global_path / "SKILL.md").exists():
                logging.debug(
                    "Skill '%s' not found in workspace '%s', falling back to global SKILLS_DIR",
                    skill_name, workspace_dir,
                )
                return global_path
        return None

    # ── 阶段 1：元数据解析，构建 XML description ────────────────────────────

    def _build_description(self) -> None:
        """
        💡 核心点：渐进式披露第一阶段
        只读 frontmatter，构建轻量 XML 注入 description。
        主 Agent 看到工具 → 知道"什么场景用什么 Skill"，但不加载完整指令。
        """
        effective_dir = self._effective_skills_dir()
        manifest_path = effective_dir / "load_skills.yaml"
        if not manifest_path.exists():
            # 找不到配置文件时，保证工具仍可被安全加载
            self.description = (
                "SkillLoaderTool 已初始化，但当前未找到 load_skills.yaml，"
                "因此暂时没有可用的 Skill。"
            )
            return

        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        except Exception as exc:  # noqa: BLE001
            # YAML 解析失败时，避免整个工具崩溃
            self.description = (
                "SkillLoaderTool 初始化失败：解析 load_skills.yaml 出错，"
                f"错误类型：{type(exc).__name__}，错误信息：{exc}"
            )
            return

        skills_conf = manifest.get("skills") or []

        xml_parts = ["<available_skills>"]
        for skill_conf in skills_conf:
            if not skill_conf.get("enabled", True):
                continue
            name = skill_conf["name"]
            skill_type = skill_conf.get("type", "task")
            # 💡 双目录查找：workspace 优先，全局回退
            skill_path = self._resolve_skill_path(name)
            if skill_path is None:
                continue

            skill_md = (skill_path / "SKILL.md").read_text()
            desc = self._extract_frontmatter_description(skill_md)

            self._skill_registry[name] = {
                "type": skill_type,
                "path": skill_path,
            }
            xml_parts.append(
                f"  <skill>\n"
                f"    <name>{name}</name>\n"
                f"    <type>{skill_type}</type>\n"
                f"    <description>{desc}</description>\n"
                f"  </skill>"
            )
        xml_parts.append("</available_skills>")

        # 💡 核心点：约束已在 SkillLoaderInput.task_context 的 Field description 中定义，
        #    这里只展示 Skill 能力清单，保持 description 简洁
        self.description = (
            "⚠️ 重要：这是你唯一的工具。所有能力（包括 memory-save、sop 等）都必须通过此工具调用，"
            "不得直接调用 skill 名称作为工具。\n\n"
            "调用方式：skill_loader(skill_name='<名称>', task_context='<任务描述>')\n"
            "skill_name 必须严格来自下方 XML 列表中的 <name> 值。\n\n"
            + "\n".join(xml_parts)
        )

    def _extract_frontmatter_description(self, content: str) -> str:
        """从 SKILL.md 的 YAML frontmatter 中提取 description 字段（最多 200 字符）"""
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return ""
        front = yaml.safe_load(match.group(1))
        desc = front.get("description", "")
        if not desc:
            return ""
        return desc[:200] + "..." if len(desc) > 200 else desc

    # ── 阶段 2：按需加载完整指令 ─────────────────────────────────────────────

    def _get_skill_instructions(self, skill_name: str) -> str:
        """
        💡 核心点：渐进式披露第二阶段
        读取完整 SKILL.md，剥离 frontmatter，拼接沙盒路径替换指令。
        结果写入 _instruction_cache，同一 Skill 只读一次文件。
        """
        if skill_name in self._instruction_cache:
            return self._instruction_cache[skill_name]

        skill_path = self._skill_registry[skill_name]["path"]
        content = (skill_path / "SKILL.md").read_text()
        # 剥离 YAML frontmatter（--- ... ---）
        stripped = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL)

        # 拼接沙盒路径替换指令，消灭 LLM 路径幻觉（工具名与参数与 AIO-Sandbox MCP 一致）
        _base = f"{SANDBOX_SKILLS_MOUNT}/{skill_name}"
        sandbox_directive = (
            f"\n\n<sandbox_execution_directive>\n"
            f"IMPORTANT:【强制约束】所有脚本和文件操作必须在 AIO-Sandbox 中执行，禁止直接操作本地文件系统。\n"
            f"此 Skill 资源已挂载至沙盒绝对路径：{_base}/\n\n"
            f"可用沙盒工具及正确用法：\n"
            f"1. sandbox_file_operations：统一文件操作（⚡ 写文件首选工具，不经过 shell 无截断风险）。\n"
            f"   参数：action（必填，'read'|'write'|'list'|'find'|'replace'|'search'）、path（必填，文件或目录绝对路径）、其余见工具说明。\n"
            f"   - 📝 写入文件（优先！）：action=\"write\", path=\"文件绝对路径\", content=\"文件完整内容\"。内容直接通过 MCP JSON 传输，无 shell 转义，不会截断。\n"
            f"   - 读取单个文件：action=\"read\", path=\"文件绝对路径\"（示例：path=\"{_base}/reference/xxx.md\"）。\n"
            f"   - 列出目录：action=\"list\", path=\"目录绝对路径\"（如 path=\"{_base}/reference\"），可选 recursive=true。\n"
            f"   - 按模式查找文件：action=\"find\", path=\"目录\", pattern=\"*.md\"。\n"
            f"2. sandbox_execute_bash：执行 Shell 命令。参数：cmd（必填，字符串）、cwd（可选，工作目录绝对路径）、timeout（可选，秒）。\n"
            f"   ⚠️ 警告：通过 bash 命令行传递大段文件内容（如 --content \"...\"）极易因 shell 特殊字符（引号、反引号、$变量等）导致内容静默截断！\n"
            f"   ✅ bash 适用场景：运行脚本、安装依赖、执行系统命令——不得用于传递大段文本内容。\n"
            f"   - 运行脚本示例：cmd=\"python {_base}/scripts/xxx.py 参数\"，如需可设 cwd=\"{_base}\"。\n"
            f"   - 安装依赖：cmd=\"pip install 包名\"，再重试任务。\n"
            f"3. sandbox_execute_code：执行代码片段（备用写文件方案）。参数：code（必填）、language（'python'|'javascript'）、timeout（可选）。\n"
            f"   - 当需要写入大文件且 sandbox_file_operations write 不可用时，用 Python 代码直接写文件，避免 shell 转义问题。\n"
            f"4. sandbox_str_replace_editor：编辑文件。参数：command（'view'|'create'|'str_replace'|'insert'）、path（文件路径）等。\n"
            f"\n"
            f"【写文件优先级】sandbox_file_operations(action='write') > sandbox_execute_code(python write) > ❌sandbox_execute_bash(--content)\n"
            f"</sandbox_execution_directive>"
        )

        result = stripped + sandbox_directive
        self._instruction_cache[skill_name] = result
        return result

    # ── Sub-Crew 执行（任务型 Skill）────────────────────────────────────────

    async def _execute_skill_async(self, skill_name: str, task_context: str) -> str:
        """核心执行路径：加载指令，按 type 分流"""
        skill_info = self._skill_registry[skill_name]
        instructions = self._get_skill_instructions(skill_name)

        if skill_info["type"] == "reference":
            # 参考型：直接返回指令文本，不启动 Sub-Crew
            return f"<skill_instructions>\n{instructions}\n</skill_instructions>"

        # 任务型：task_context 为空时，返回指令帮助 Agent 理解 Skill 后再调用
        if not task_context.strip():
            return (
                f"<skill_instructions>\n{instructions}\n</skill_instructions>\n\n"
                "⚠️ 这是任务型 Skill（type: task），需要 task_context 才能执行。\n"
                "请在下次调用时传入完整的 task_context，包含：\n"
                "1. 要执行的具体操作（如：发送邮件/读取邮箱）\n"
                "2. 预期输出格式（JSON schema，必须包含 errcode 和 errmsg 字段）\n"
                "3. 所有必要的参数值（收件人、发件人、消息内容等）"
            )

        # 任务型：启动独立 Sub-Crew，在沙盒中执行
        # 💡 核心点：每次 build_skill_crew() 返回新实例，防止状态污染
        crew = build_skill_crew(
            skill_name=skill_name,
            skill_instructions=instructions,
            mount_desc=self.sandbox_mount_desc,  # 💡 透传挂载描述，m3l20 使用自定义挂载
            mcp_url=self.sandbox_mcp_url,        # 💡 透传 MCP URL，m4l25 各角色使用独立端口
        )

        # 💡 防止 CrewAI 模板引擎对 SKILL.md 中的 {xxx} 占位符报错
        # （如 mailbox-ops SKILL.md 中的 {role}.json）
        # 策略：预扫描所有 agent/task 字段，把不在 inputs 中的变量
        #       设为自引用（{role} → {role}），保持文本不变
        base_inputs: dict[str, str] = {
            "task_context": task_context,
            "skill_name": skill_name,
        }
        all_text = ""
        for _a in crew.agents:
            all_text += (_a.role or "") + " " + (_a.goal or "") + " " + (_a.backstory or "") + " "
        for _t in crew.tasks:
            all_text += (_t.description or "") + " " + (_t.expected_output or "") + " "
        for var in re.findall(r"\{([A-Za-z_][A-Za-z0-9_\-]*)\}", all_text):
            if var not in base_inputs:
                base_inputs[var] = "{" + var + "}"

        result = await crew.akickoff(inputs=base_inputs)
        return str(result)

    # ── 异步路径（FastAPI / akickoff 调用链）────────────────────────────────

    async def _arun(self, skill_name: str, task_context: str) -> str:
        """
        💡 核心点：FastAPI 异步调用链的主路径，直接 await Sub-Crew
        CrewAI 在 arun() 内部调用 _arun()，框架自动选路
        """
        if skill_name not in self._skill_registry:
            return f"错误：未找到 Skill '{skill_name}'，可用：{list(self._skill_registry.keys())}"
        return await self._execute_skill_async(skill_name, task_context)

    # ── 同步路径（脚本 / 测试场景 fallback）─────────────────────────────────

    def _run(self, skill_name: str, task_context: str) -> str:
        """
        💡 核心点：用 ThreadPoolExecutor 在新线程中运行独立 event loop，
        规避主线程已有 event loop 时 asyncio.run() 报
        'cannot run nested event loop' 的问题
        """
        if skill_name not in self._skill_registry:
            return f"错误：未找到 Skill '{skill_name}'，可用：{list(self._skill_registry.keys())}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                self._execute_skill_async(skill_name, task_context),
            )
            return future.result()