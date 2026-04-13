"""
课程：20｜文件系统记忆——让 Agent 自己写记忆、自己学技能
统一示例文件：m3l20_file_memory.py

演示三个核心 Skill：
  - memory-save：将偏好/事实持久化到 workspace/ 文件
  - skill-creator：将 SOP 固化为可复用 SKILL.md
  - memory-governance：审计 + 清理记忆文件与 skills/ 目录

与 m3l19 的区别：
  - 移除 FileWriterTool / FileReadTool（文件操作委托给沙盒 Sub-Crew）
  - 加入 SkillLoaderTool(sandbox_mount_desc=M3L20_SANDBOX_MOUNT_DESC)
  - 继承 m3l19 的 Bootstrap / 剪枝 / 压缩纯函数，一行不改

运行前：
  1. 启动 m3l20 专用沙盒：docker compose -f sandbox-docker-compose.yaml up -d
  2. 确保 workspace/ 下有 soul.md / user.md / agent.md / memory.md
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

from crewai import Agent, Crew, LLM, Task
from crewai.hooks import LLMCallHookContext, before_llm_call
from crewai.project import CrewBase, agent, crew, task

# ── 项目根加入 sys.path，复用 llm / tools ────────────────────────────────────
_M3L20_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT = _M3L20_DIR.parent
for _p in [str(_M3L20_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm import aliyun_llm                           # noqa: E402
from tools.skill_loader_tool import SkillLoaderTool  # noqa: E402
from tools import BaiduSearchTool                    # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# 路径常量
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_DIR = _M3L20_DIR / "workspace"
SESSIONS_DIR  = WORKSPACE_DIR / "sessions"
# 💡 SKILLS_DIR 不在这里定义——复用 SkillLoaderTool 里的共享常量（crewai_mas_demo/skills/）

# ─────────────────────────────────────────────────────────────────────────────
# m3l20 沙盒挂载描述（传给 SkillLoaderTool）
# 与 m2l16 DEFAULT_SANDBOX_MOUNT_DESC 的区别：
#   - workspace 整体挂载为 :rw（memory-save 可以写任意 workspace 文件）
#   - 额外挂载 ../skills → /mnt/skills:rw（skill-creator 可以写新 SKILL.md）
# ─────────────────────────────────────────────────────────────────────────────

M3L20_SANDBOX_MOUNT_DESC = (
    "1. 所有的操作必须在沙盒中执行，不得操作本地文件系统。\n"
    "   当前已挂载的目录：\n"
    "   - ./workspace:/workspace:rw（可读写，memory-save 写记忆文件到这里）\n"
    "   - ../skills:/mnt/skills:rw（可读写，skill-creator 写 SKILL.md 到这里）\n\n"
    "2. 记忆文件读写规范：\n"
    f"   - 读取：用沙盒绝对路径 /workspace/<filename>（如 /workspace/user.md）\n"
    "   - 写入：同上，写前必须先 read 目标文件，确认无重复内容\n\n"
    "3. Skill 文件写入规范：\n"
    f"   - 目录：/mnt/skills/<skill-name>/SKILL.md\n"
    "   - 注册：同时更新 /mnt/skills/load_skills.yaml\n\n"
    "4. 如遇依赖缺失，先在沙盒中安装再继续"
)

# ─────────────────────────────────────────────────────────────────────────────
# 纯函数（直接继承 m3l19，无修改）
# ─────────────────────────────────────────────────────────────────────────────

# 可调整的核心参数（与 m3l19 保持一致）
PRUNE_KEEP_TURNS   = 10 #保留回合修剪
COMPRESS_THRESHOLD = 0.45 # double 压缩阈值
CHUNK_TOKENS       = 2000 # 记忆文件过大时的切分粒度，单位 token（与模型上下文限制相关）
FRESH_KEEP_TURNS   = 10 # 新鲜度剪枝时保留的回合数（越大越保守，越小越激进）
MODEL_CTX_LIMIT    = 32000 # 模型上下文限制，单位 token（根据实际使用的模型调整，预留部分空间给工具结果等）


def build_bootstrap_prompt(workspace_dir: Path) -> str:
    """
    加载 workspace 导航骨架：soul + user_profile + agent_rules + memory_index。
    memory.md 截取前 200 行，防止索引膨胀。
    """
    parts: list[str] = []

    for fname, tag in [
        ("soul.md",   "soul"),
        ("user.md",   "user_profile"),
        ("agent.md",  "agent_rules"),
    ]:
        path = workspace_dir / fname
        if path.exists():
            parts.append(
                f"<{tag}>\n{path.read_text(encoding='utf-8').strip()}\n</{tag}>"
            )

    # 💡 核心点：memory.md 200 行上限——只注入导航索引，真正的记忆按需 read
    memory_path = workspace_dir / "memory.md"
    if memory_path.exists():
        lines = memory_path.read_text(encoding="utf-8").splitlines()[:200]
        parts.append(
            f"<memory_index>\n{chr(10).join(lines)}\n</memory_index>"
        )

    return "\n\n".join(parts)

def load_session_ctx(session_id: str, sessions_dir: Path = SESSIONS_DIR) -> list[dict]:
    """读取压缩 context 快照，用于 session 恢复"""
    p = sessions_dir / f"{session_id}_ctx.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def save_session_ctx(
    session_id: str,
    messages: list[dict],
    sessions_dir: Path = SESSIONS_DIR,
) -> None:
    """覆盖写入当前压缩 context 快照"""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / f"{session_id}_ctx.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def append_session_raw(
    session_id: str,
    messages: list[dict],
    sessions_dir: Path = SESSIONS_DIR,
) -> None:
    """追加一批消息到原始完整历史（append-only JSONL）"""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(sessions_dir / f"{session_id}_raw.jsonl", "a", encoding="utf-8") as f:
        for msg in messages:
            record = {**msg, "ts": ts}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def prune_tool_results(
    messages: list[dict],
    keep_turns: int = PRUNE_KEEP_TURNS,
) -> None:
    """
    in-place 剪枝：keep_turns 之前的 tool result 替换为 [已剪枝]，释放 context 空间。
    💡 核心点：保留消息占位和 tool_call_id，维持 OpenAI 消息格式合法性。
    """
    user_indices = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(user_indices) <= keep_turns:
        return
    cutoff_idx = user_indices[-keep_turns]
    for i in range(cutoff_idx):
        if messages[i].get("role") == "tool":
            messages[i]["content"] = "[已剪枝]"

def chunk_by_tokens(
    messages: list[dict],
    chunk_tokens: int = CHUNK_TOKENS,
) -> list[list[dict]]:
    """按近似 token 数切分消息列表（中文 1 字 ≈ 1 token，取保守值 len // 2）"""
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
    """用轻量模型生成摘要，节省成本（可 mock 用于测试）"""
    from config import llm_config
    summary_model = llm_config.get_default_summary_model()
    summary_llm = LLM(model=summary_model)
    history = "\n".join(
        f"{m.get('role', '')}: {str(m.get('content', ''))[:300]}"
        for m in messages
    )
    return summary_llm.call([
        {"role": "user", "content": _SUMMARY_PROMPT.format(history=history)}
    ])

def maybe_compress(
    messages: list[dict],
    context: LLMCallHookContext,
    fresh_keep_turns: int = FRESH_KEEP_TURNS,
    chunk_tokens: int = CHUNK_TOKENS,
    compress_threshold: float = COMPRESS_THRESHOLD,
) -> None:
    """
    in-place 压缩。超过 compress_threshold 时：
      ① 保留 system 消息和最近 fresh_keep_turns 轮原文
      ② 更早的消息分块，调 qwen3-turbo 生成摘要替换
    """
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

    chunks       = chunk_by_tokens(old_msgs, chunk_tokens)
    summary_msgs = [
        {
            "role":    "system",
            "content": f"<context_summary>\n{_summarize_chunk(chunk)}\n</context_summary>",
        }
        for chunk in chunks
    ]

    messages.clear()
    messages.extend(system_msgs + summary_msgs + fresh_msgs)


@CrewBase
class JackClawCrew:
    """
    JackClaw 个人助手（第20课）

    与 m3l19 的关键区别：
    - tools：SkillLoaderTool（传入 M3L20_SANDBOX_MOUNT_DESC）+ BaiduSearchTool
    - 移除 FileWriterTool / FileReadTool：文件操作全部委托给 AIO-Sandbox Sub-Crew
    - @before_llm_call hook 完全继承 m3l19，一行不改
    """

    def __init__(self, session_id: str, user_message: str) -> None:
        self.session_id      = session_id
        self.user_message    = user_message
        self._session_loaded = False
        self._last_msgs: list[dict] = []
        self._history_len    = 0

    @agent
    def assistant_agent(self) -> Agent:
        from config import llm_config
        default_model = llm_config.get_default_model()
        
        return Agent(
            role      = "JackClaw 个人助手",
            goal      = "帮助晓寒高效完成各类任务，严谨、结果导向",
            backstory = build_bootstrap_prompt(WORKSPACE_DIR),   # 💡 Bootstrap
            llm       = aliyun_llm.AliyunLLM(
                model   = default_model,
                api_key = os.getenv("QWEN_API_KEY"),
                region  = "cn",
            ),
            tools = [
                # 💡 核心点：传入 m3l20 挂载描述，其余行为与 m2l16 完全相同
                SkillLoaderTool(sandbox_mount_desc=M3L20_SANDBOX_MOUNT_DESC),
                BaiduSearchTool(),
                # 没有 FileWriterTool / FileReadTool
                # 文件操作委托给 AIO-Sandbox Sub-Crew（/workspace:rw 沙盒）
            ],
            verbose  = True,
            max_iter = 50,
        )
    @task
    def assistant_task(self) -> Task:
        return Task(
            description     = "{user_request}",
            expected_output = "针对用户请求的完整回复，文件操作已通过 Skill 在沙盒中完成",
            agent           = self.assistant_agent(),
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents  = self.agents,
            tasks   = self.tasks,
            verbose = True,
        )
    
    @before_llm_call
    def before_llm_hook(self, context: LLMCallHookContext) -> bool | None:
        """
        每次 LLM 调用前拦截，in-place 修改 context.messages。
        首次调用恢复历史 session，每次调用执行剪枝 + 压缩。
        """
        if not self._session_loaded:
            self._restore_session(context)
            self._session_loaded = True

        self._last_msgs = context.messages
        prune_tool_results(context.messages)
        maybe_compress(context.messages, context)
        return None

    def _restore_session(self, context: LLMCallHookContext) -> None:
        """从 ctx.json 恢复历史 context，追加当前轮 user 消息"""
        history = load_session_ctx(self.session_id)
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

SESSION_ID = "demo_m3-20"

DEMO_ROUNDS = [
    (
        "记忆保存",
        "我以后写 Python 代码，注释尽量用中文，回复也控制在 200 字以内。把这两条偏好记录下来。",
    ),
    (
        "技能固化",
        (
            "我发现每次分析港股都要做同样几步：查实时行情 → 看近期新闻 → 写估值分析。"
            "把这个 SOP 保存为一个叫 analyze-hk-stock 的 Skill，以后直接调用。"
        ),
    ),
    (
        "记忆治理",
        "帮我审计一下 workspace/ 和 skills/ 目录，有没有需要清理的内容，生成治理报告。",
    ),
]


def main() -> None:
    print(f"\n{'='*60}")
    print("JackClaw 助手 - 第20课：文件系统记忆")
    print(f"{'='*60}")
    print(f"Session ID : {SESSION_ID}")
    print(f"Workspace  : {WORKSPACE_DIR}")
    saved = load_session_ctx(SESSION_ID)
    if saved:
        print(f"历史消息   : {len(saved)} 条（将恢复上下文）")
    else:
        print("历史消息   : 无（全新 session）")
    # return
    for i, (label, message) in enumerate(DEMO_ROUNDS, 1):
        print(f"\n{'─'*60}")
        print(f"Round {i}/{len(DEMO_ROUNDS)}  [{label}]")
        print(f"用户消息   : {message}")
        print(f"{'─'*60}\n")
        #continue
        crew_instance = JackClawCrew(SESSION_ID, message)
        result = crew_instance.crew().kickoff(
            inputs={"user_request": message}
        )
        ## 如果存在历史消息，则提取新增的消息片段并更新会话状态
        if crew_instance._last_msgs:
            new_msgs = list(crew_instance._last_msgs)[crew_instance._history_len:]
            append_session_raw(SESSION_ID, new_msgs)
            save_session_ctx(SESSION_ID, list(crew_instance._last_msgs))

        print(f"\n{'─'*60}")
        print(f"回复：\n{result.raw}")

    print(f"\n{'='*60}")
    print("Session 文件：")
    print(f"  ctx  → {SESSIONS_DIR / f'{SESSION_ID}_ctx.json'}")
    print(f"  raw  → {SESSIONS_DIR / f'{SESSION_ID}_raw.jsonl'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()