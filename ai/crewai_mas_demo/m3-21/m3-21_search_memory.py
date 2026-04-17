"""
课程：21｜搜索驱动的记忆系统——当文件索引不够用时
统一示例文件：m3-21_search_memory.py

演示两个核心能力：
  1. 建索引：每轮对话结束后异步触发 indexer，写入 pgvector
  2. 搜索：search_memory Skill（task 型），Sub-Crew 自主写 SQL 混合检索

与 m3l20 的区别：
  - 新增 indexer 异步后台任务（每轮对话后触发）
  - 新增 search_memory task Skill（混合检索）
  - 继承 m3-20 的 Bootstrap / 剪枝 / 压缩 / SkillLoaderTool，一行不改

运行前：
  1. 启动 pgvector：docker compose -f pgvector-docker-compose.yaml up -d
  2. 启动 m3-20 沙盒（search_memory Skill 需要）：
     docker compose -f ../m3-20/sandbox-docker-compose.yaml up -d
  3. 设置环境变量：QWEN_API_KEY=xxx
"""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import sys
import time
from pathlib import Path

from crewai import Agent, Crew, LLM, Task
from crewai.hooks import LLMCallHookContext, before_llm_call
from crewai.project import CrewBase, agent, crew, task

# ── 项目根加入 sys.path，复用 llm / tools ────────────────────────────────────
_M3L21_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT = _M3L21_DIR.parent
for _p in [str(_M3L21_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm import aliyun_llm                           # noqa: E402
from tools.skill_loader_tool import SkillLoaderTool  # noqa: E402
from tools import BaiduSearchTool                    # noqa: E402
from indexer import async_index_turn                 # noqa: E402
# ─────────────────────────────────────────────────────────────────────────────
# 路径常量
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_DIR = _M3L21_DIR.parent / "m3-20" / "workspace"   # 复用 m3-20 workspace
SESSIONS_DIR  = WORKSPACE_DIR / "sessions"
SKILLS_DIR    = _M3L21_DIR / "skills"                        # 兼容保留：当前实际由 ../skills 挂载并提供 search_memory

# ─────────────────────────────────────────────────────────────────────────────
# 沙盒挂载描述（在 m3l20 基础上增加 search_memory skill）
# ─────────────────────────────────────────────────────────────────────────────

M3L21_SANDBOX_MOUNT_DESC = (
    "1. 所有的操作必须在沙盒中执行，不得操作本地文件系统。\n"
    "   当前已挂载的目录：\n"
    "   - ./workspace:/workspace:rw（可读写，memory-save 写记忆文件到这里）\n"
    "   - ../skills:/mnt/skills:ro（只读，共享所有 skills，包括 search_memory）\n\n"
    "2. 记忆文件读写规范：\n"
    "   - 读取：用沙盒绝对路径 /workspace/<filename>\n"
    "   - 写入：同上，写前必须先 read 目标文件，确认无重复内容\n\n"
    "3. search_memory Skill 调用规范：\n"
    "   - Skill 文档：/mnt/skills/search_memory/SKILL.md\n"
    "   - 执行脚本：python /mnt/skills/search_memory/scripts/search.py\n"
    "   - 需要环境变量：MEMORY_DB_DSN、QWEN_API_KEY\n\n"
    "4. 如遇依赖缺失，先在沙盒中安装再继续"
)

# ─────────────────────────────────────────────────────────────────────────────
# 纯函数（完整继承 m3l20，一行不改）
# ─────────────────────────────────────────────────────────────────────────────
PRUNE_KEEP_TURNS   = 10
COMPRESS_THRESHOLD = 0.45
CHUNK_TOKENS       = 2000
FRESH_KEEP_TURNS   = 10
MODEL_CTX_LIMIT    = 32000

def build_bootstrap_prompt(workspace_dir: Path) -> str:
    parts: list[str] = []
    for fname, tag in [
        ("soul.md",  "soul"),
        ("user.md",  "user_profile"),
        ("agent.md", "agent_rules"),
    ]:
        path = workspace_dir / fname
        if path.exists():
            parts.append(f"<{tag}>\n{path.read_text(encoding='utf-8').strip()}\n</{tag}>")

    memory_path = workspace_dir / "memory.md"
    if memory_path.exists():
        lines = memory_path.read_text(encoding="utf-8").splitlines()[:200]
        parts.append(f"<memory_index>\n{chr(10).join(lines)}\n</memory_index>")

    return "\n\n".join(parts)


def load_session_ctx(session_id: str, sessions_dir: Path = SESSIONS_DIR) -> list[dict]:
    p = sessions_dir / f"{session_id}_ctx.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save_session_ctx(session_id: str, messages: list[dict], sessions_dir: Path = SESSIONS_DIR) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / f"{session_id}_ctx.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def append_session_raw(session_id: str, messages: list[dict], sessions_dir: Path = SESSIONS_DIR) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(sessions_dir / f"{session_id}_raw.jsonl", "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps({**msg, "ts": ts}, ensure_ascii=False) + "\n")


def prune_tool_results(messages: list[dict], keep_turns: int = PRUNE_KEEP_TURNS) -> None:
    user_indices = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(user_indices) <= keep_turns:
        return
    cutoff_idx = user_indices[-keep_turns]
    for i in range(cutoff_idx):
        if messages[i].get("role") == "tool":
            messages[i]["content"] = "[已剪枝]"


def chunk_by_tokens(messages: list[dict], chunk_tokens: int = CHUNK_TOKENS) -> list[list[dict]]:
    if not messages:
        return []
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0
    for msg in messages:
        msg_tokens = len(str(msg.get("content", ""))) // 2
        if current_tokens + msg_tokens > chunk_tokens and current:
            chunks.append(current)
            current = [msg]
            current_tokens = msg_tokens
        else:
            current.append(msg)
            current_tokens += msg_tokens
    if current:
        chunks.append(current)
    return chunks

_SUMMARY_PROMPT = """\
将以下对话历史压缩为结构化摘要，只保留关键信息：
1. 用户目标：这段对话要完成什么
2. 关键事实：重要的结论、文件路径、操作结果
3. 未完成事项：尚未完成的任务（如有）

禁止包含：中间过程、失败尝试、重复内容。

对话历史：
{history}
"""


def _summarize_chunk(messages: list[dict]) -> str:
    # 使用与主 Agent 相同的 qwen3-max，避免环境中找不到 qwen3-turbo 导致压缩失败
    summary_llm = LLM(model="qwen3-max")
    history = "\n".join(
        f"{m.get('role', '')}: {str(m.get('content', ''))[:300]}" for m in messages
    )
    return summary_llm.call([{"role": "user", "content": _SUMMARY_PROMPT.format(history=history)}])


def maybe_compress(
    messages: list[dict],
    context: LLMCallHookContext,
    fresh_keep_turns: int = FRESH_KEEP_TURNS,
    chunk_tokens: int = CHUNK_TOKENS,
    compress_threshold: float = COMPRESS_THRESHOLD,
) -> None:
    model_limit   = getattr(context.llm, "context_window_size", MODEL_CTX_LIMIT)
    approx_tokens = sum(len(str(m.get("content", ""))) // 2 for m in messages)
    if approx_tokens / model_limit < compress_threshold:
        return

    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system  = [m for m in messages if m.get("role") != "system"]
    user_indices = [i for i, m in enumerate(non_system) if m.get("role") == "user"]
    if len(user_indices) <= fresh_keep_turns:
        return

    cutoff     = user_indices[-fresh_keep_turns]
    old_msgs   = non_system[:cutoff]
    fresh_msgs = non_system[cutoff:]
    chunks     = chunk_by_tokens(old_msgs, chunk_tokens)
    summary_msgs = [
        {"role": "system", "content": f"<context_summary>\n{_summarize_chunk(chunk)}\n</context_summary>"}
        for chunk in chunks
    ]
    messages.clear()
    messages.extend(system_msgs + summary_msgs + fresh_msgs)


# ─────────────────────────────────────────────────────────────────────────────
# JackClawCrew（第21课：在 m3l20 基础上增加异步建索引）
# ─────────────────────────────────────────────────────────────────────────────

@CrewBase
class JackClawCrew:
    """
    JackClaw 个人助手（第21课）

    与 m3l20 的关键区别：
    - 每轮对话结束后，异步触发 indexer 建索引（不阻塞主流程）
    - 新增 search_memory task Skill，支持混合检索历史记忆
    - Bootstrap / hook / SkillLoaderTool 完整继承 m3l20
    """

    def __init__(self, session_id: str, user_message: str, routing_key: str = "p2p:demo") -> None:
        self.session_id      = session_id
        self.user_message    = user_message
        self.routing_key     = routing_key
        self._session_loaded = False
        self._last_msgs: list[dict] = []
        self._history_len    = 0
        self._turn_start_ts  = int(time.time() * 1000)

    @agent
    def assistant_agent(self) -> Agent:
        return Agent(
            role      = "JackClaw 个人助手",
            goal      = "帮助Jack高效完成各类任务，严谨、结果导向",
            backstory = build_bootstrap_prompt(WORKSPACE_DIR),
            llm       = aliyun_llm.AliyunLLM(
                model   = "qwen3-max",
                api_key = os.getenv("QWEN_API_KEY"),
                region  = "cn",
            ),
            tools = [
                SkillLoaderTool(sandbox_mount_desc=M3L21_SANDBOX_MOUNT_DESC),
                BaiduSearchTool(),
            ],
            verbose  = True,
            max_iter = 50,
        )

    @task
    def assistant_task(self) -> Task:
        return Task(
            description     = "{user_request}",
            expected_output = "针对用户请求的完整回复",
            agent           = self.assistant_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, verbose=True)

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
        history = load_session_ctx(self.session_id)
        self._history_len = len(history)
        if not history:
            return
        current_user_msg = next(
            (m for m in reversed(context.messages) if m.get("role") == "user"), {}
        )
        context.messages.clear()
        context.messages.extend(history)
        if current_user_msg:
            context.messages.append(current_user_msg)

    async def run_and_index(self) -> str:
        """
        执行一轮对话，结束后异步触发建索引。
        💡 核心点：asyncio.create_task() 必须在 async 函数内调用，后台触发不阻塞返回
        """
        result = self.crew().kickoff(inputs={"user_request": self.user_message})

        # 持久化 session
        if self._last_msgs:
            new_msgs = list(self._last_msgs)[self._history_len:]
            append_session_raw(self.session_id, new_msgs)
            save_session_ctx(self.session_id, list(self._last_msgs))

        # 💡 核心点：asyncio.create_task() 在 async 上下文内才合法，后台建索引不阻塞
        assistant_reply = result.raw
        asyncio.create_task(
            async_index_turn(
                session_id      = self.session_id,
                routing_key     = self.routing_key,
                user_message    = self.user_message,
                assistant_reply = assistant_reply,
                turn_ts         = self._turn_start_ts,
            )
        )

        return assistant_reply
    
# ─────────────────────────────────────────────────────────────────────────────
# 演示参数 & main
# ─────────────────────────────────────────────────────────────────────────────
SESSION_ID   = "demo_m3_21"
ROUTING_KEY  = "p2p:ou_demo"

DEMO_ROUNDS = [
    (
        "普通任务（建索引）",
        "帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。",
    ),
    (
        "普通任务（建索引）",
        "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
    ),
    (
        "语义搜索（跨 session 召回）",
        "我之前让你查过一个向量数据库的对比，帮我找一下那次的结论。不要只凭当前对话上下文回忆，必须调用 search_memory Skill，从 pgvector 历史记忆中检索并给出结果。",
    ),
]


async def main_async() -> None:
    print(f"\n{'='*60}")
    print("XiaoPaw 助手 - 第21课：搜索驱动的记忆系统")
    print(f"{'='*60}")
    print(f"Session ID  : {SESSION_ID}")
    print(f"Routing Key : {ROUTING_KEY}")

    for i, (label, message) in enumerate(DEMO_ROUNDS, 1):
        print(f"\n{'─'*60}")   


        print(f"Round {i}/{len(DEMO_ROUNDS)}  [{label}]")
        print(f"用户消息    : {message}")
        print(f"{'─'*60}\n")
        return 
        crew_instance = JackClawCrew(SESSION_ID, message, ROUTING_KEY)
        reply = await crew_instance.run_and_index()

        print(f"\n{'─'*60}")
        print(f"回复：\n{reply}")

        # 等待后台索引任务完成（演示用，生产中不需要等）
        await asyncio.sleep(2)

    print(f"\n{'='*60}")
    print("演示完成。记忆已写入 pgvector，可用 search_memory Skill 搜索。")
    print(f"{'='*60}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()