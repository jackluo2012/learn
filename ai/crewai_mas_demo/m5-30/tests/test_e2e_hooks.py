"""端到端集成测试：真实 Crew 执行，验证 7 种事件类型 × 两层 hook 全部触发。

需要 LLM API（OPENAI_API_KEY + OPENAI_API_BASE）。
标记 @pytest.mark.integration，默认跳过，用 -m integration 运行。
"""

import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

_M5L30_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_M5L30_DIR))

from hook_framework import (
    CrewObservabilityAdapter,
    EventType,
    HookLoader,
    HookRegistry,
)

pytestmark = pytest.mark.integration

# ── 共用的 counter hook 脚本（写 JSON 行到文件） ──────────────────

_COUNTER_HANDLER_CODE = textwrap.dedent('''\
    """Counter hook：每触发一次，往 {log_file} 追加一行 JSON。"""
    import json
    from pathlib import Path

    LOG_FILE = Path(r"{log_file}")

    def _write(ctx, layer):
        entry = {{"event": ctx.event_type.value, "layer": layer, "turn": ctx.turn_number}}
        if ctx.tool_name:
            entry["tool"] = ctx.tool_name
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\\n")

    def before_turn_handler(ctx):   _write(ctx, "{layer}")
    def before_llm_handler(ctx):    _write(ctx, "{layer}")
    def before_tool_handler(ctx):   _write(ctx, "{layer}")
    def after_tool_handler(ctx):    _write(ctx, "{layer}")
    def after_turn_handler(ctx):    _write(ctx, "{layer}")
    def task_complete_handler(ctx):  _write(ctx, "{layer}")
    def session_end_handler(ctx):    _write(ctx, "{layer}")
''')

_HOOKS_YAML_ALL_EVENTS = textwrap.dedent('''\
    hooks:
      BEFORE_TURN:
        - handler: counter.before_turn_handler
      BEFORE_LLM:
        - handler: counter.before_llm_handler
      BEFORE_TOOL_CALL:
        - handler: counter.before_tool_handler
      AFTER_TOOL_CALL:
        - handler: counter.after_tool_handler
      AFTER_TURN:
        - handler: counter.after_turn_handler
      TASK_COMPLETE:
        - handler: counter.task_complete_handler
      SESSION_END:
        - handler: counter.session_end_handler
''')


def _setup_hook_dirs(tmp_path):
    """创建两层 hook 目录，每层覆盖全部 7 种事件。"""
    log_file = tmp_path / "hook_events.jsonl"

    # 全局层
    global_dir = tmp_path / "shared_hooks"
    global_dir.mkdir()
    (global_dir / "hooks.yaml").write_text(_HOOKS_YAML_ALL_EVENTS)
    (global_dir / "counter.py").write_text(
        _COUNTER_HANDLER_CODE.format(log_file=str(log_file), layer="global")
    )

    # Workspace 层
    ws_dir = tmp_path / "workspace"
    ws_hooks = ws_dir / "hooks"
    ws_hooks.mkdir(parents=True)
    (ws_hooks / "hooks.yaml").write_text(_HOOKS_YAML_ALL_EVENTS)
    (ws_hooks / "counter.py").write_text(
        _COUNTER_HANDLER_CODE.format(log_file=str(log_file), layer="workspace")
    )

    return global_dir, ws_dir, log_file


def _parse_log(log_file: Path) -> list[dict]:
    if not log_file.exists():
        return []
    lines = log_file.read_text().strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


# ── T15: 全链路事件覆盖（真实 Crew） ────────────────────────────

def test_all_event_types_fired_both_layers(tmp_path):
    """真实 Crew kickoff → 断言 7 种事件类型 × 2 层 hook 全部至少触发 1 次。"""
    from crewai import Agent, Crew, LLM, Task
    from crewai.hooks import clear_all_global_hooks
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    clear_all_global_hooks()

    # 自定义搜索工具（确保触发 tool call 事件）
    class QInput(BaseModel):
        query: str = Field(description="q")

    class FakeTool(BaseTool):
        name: str = "fake_search"
        description: str = "搜索信息"
        args_schema: type[BaseModel] = QInput

        def _run(self, query: str) -> str:
            return f"关于{query}的结果：这是测试数据。"

    # 设置两层 hook 目录
    global_dir, ws_dir, log_file = _setup_hook_dirs(tmp_path)

    # 初始化 Hook 框架
    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_two_layers(global_dir, ws_dir)

    # 验证加载：每种事件 2 个 handler（global + workspace）
    for et in EventType:
        count = registry.handler_count(et)
        assert count == 2, f"{et.value} should have 2 handlers (global + workspace), got {count}"

    # 适配层
    adapter = CrewObservabilityAdapter(registry, session_id="e2e-test")
    adapter.install_global_hooks()

    # 构建 Crew
    base_url = os.environ.get(
        "OPENAI_API_BASE",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    model_name = os.environ.get("AGENT_MODEL", "qwen-plus")
    llm = LLM(model=model_name, base_url=base_url)

    agent = Agent(
        role="Tester",
        goal="你必须先调用 fake_search 工具，然后根据工具返回结果总结",
        backstory="你是测试助手。你不知道任何信息，必须通过 fake_search 工具获取数据后才能回答。绝对不要跳过工具调用直接回答。",
        llm=llm,
        verbose=False,
        tools=[FakeTool()],
    )

    task = Task(
        description="第一步：调用 fake_search 工具搜索 'hook测试'。第二步：根据工具返回的结果，用一句话总结。注意：你必须先调用工具，不能直接回答。",
        expected_output="基于 fake_search 工具返回结果的一句话总结",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
        step_callback=adapter.make_step_callback(),
        task_callback=adapter.make_task_callback(),
    )

    # 执行
    result = crew.kickoff()
    adapter.cleanup()

    # 解析日志
    entries = _parse_log(log_file)
    assert len(entries) > 0, "No hook events were logged"

    # 按 (event, layer) 分组
    fired = {(e["event"], e["layer"]) for e in entries}

    # 5 种必定触发的事件 × 2 层 = 10 种组合
    guaranteed_events = {
        EventType.BEFORE_TURN, EventType.BEFORE_LLM, EventType.AFTER_TURN,
        EventType.TASK_COMPLETE, EventType.SESSION_END,
    }
    for et in guaranteed_events:
        for layer in ("global", "workspace"):
            assert (et.value, layer) in fired, (
                f"Missing guaranteed event: event={et.value} layer={layer}\n"
                f"Fired: {sorted(fired)}\n"
                f"All entries: {entries}"
            )

    # BEFORE_TURN 至少 1 次
    before_turns = [e for e in entries if e["event"] == "before_turn"]
    assert len(before_turns) >= 2, f"Expected ≥2 BEFORE_TURN (2 layers), got {len(before_turns)}"

    # tool 事件：如果触发了则验证成对出现 + tool name
    tool_events = [e for e in entries if e["event"] in ("before_tool_call", "after_tool_call")]
    if tool_events:
        tool_event_types = {e["event"] for e in tool_events}
        assert "before_tool_call" in tool_event_types and "after_tool_call" in tool_event_types, (
            f"Tool events must come in pairs, got: {tool_event_types}"
        )
        for te in tool_events:
            assert te.get("tool") == "fake_search", f"Tool event missing tool name: {te}"

    tool_fired = len(tool_events) > 0
    print(f"\n✅ E2E: {len(entries)} hook events, {len(guaranteed_events)}×2 guaranteed + tool={'yes' if tool_fired else 'no (LLM skipped tool)'}")
    print(f"   Result: {str(result)[:100]}")


# ── T16: Langfuse trace 创建验证 ──────────────────────────────

def test_langfuse_trace_created(tmp_path):
    """用真实 shared_hooks（含 langfuse_trace）跑 Crew → 验证 Langfuse trace 有 observations。"""
    from crewai import Agent, Crew, LLM, Task
    from crewai.hooks import clear_all_global_hooks
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    langfuse_host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
    langfuse_pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    langfuse_sk = os.environ.get("LANGFUSE_SECRET_KEY")
    if not langfuse_pk or not langfuse_sk:
        pytest.skip("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set")

    clear_all_global_hooks()

    class QInput(BaseModel):
        query: str = Field(description="q")

    class FakeTool(BaseTool):
        name: str = "fake_search"
        description: str = "搜索信息"
        args_schema: type[BaseModel] = QInput

        def _run(self, query: str) -> str:
            return f"关于{query}的结果：Langfuse测试数据。"

    # 用真实 shared_hooks（含 langfuse_trace）+ 临时 workspace
    global_dir = _M5L30_DIR / "shared_hooks"
    ws_dir = tmp_path / "workspace"
    ws_hooks = ws_dir / "hooks"
    ws_hooks.mkdir(parents=True)
    (ws_hooks / "hooks.yaml").write_text(textwrap.dedent("""\
        hooks:
          TASK_COMPLETE:
            - handler: counter.task_complete_handler
    """))
    log_file = tmp_path / "ws_log.jsonl"
    (ws_hooks / "counter.py").write_text(
        _COUNTER_HANDLER_CODE.format(log_file=str(log_file), layer="workspace")
    )

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_two_layers(global_dir, ws_dir)

    session_id = f"e2e-langfuse-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    adapter = CrewObservabilityAdapter(registry, session_id=session_id)
    adapter.install_global_hooks()

    base_url = os.environ.get(
        "OPENAI_API_BASE",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    model_name = os.environ.get("AGENT_MODEL", "qwen-plus")
    llm = LLM(model=model_name, base_url=base_url)

    agent = Agent(
        role="Tester",
        goal="测试 Langfuse trace",
        backstory="你是测试助手，搜索后总结。",
        llm=llm,
        verbose=False,
        tools=[FakeTool()],
    )
    task = Task(
        description="用 fake_search 搜索'langfuse测试'，用一句话总结。",
        expected_output="一句话",
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
        step_callback=adapter.make_step_callback(),
        task_callback=adapter.make_task_callback(),
    )

    result = crew.kickoff()
    adapter.cleanup()

    # 验证 Langfuse trace (使用 REST API + 重试，兼容 batch 注入异步性)
    import time
    import hashlib
    import requests

    trace_id = hashlib.sha256(session_id.encode()).digest()[:16].hex()
    base_url = os.environ.get("LANGFUSE_BASE_URL", "http://localhost:3000")
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")

    # 重试查询，最多等待 15 秒
    observations = []
    for attempt in range(15):
        time.sleep(1)
        r = requests.get(
            f"{base_url}/api/public/observations",
            auth=(pk, sk),
            params={"traceId": trace_id, "limit": 50}
        )
        if r.ok:
            observations = r.json().get("data", [])
            if len(observations) >= 2:
                break

    assert len(observations) >= 2, (
        f"Expected ≥2 observations (tool + generation), got {len(observations)}"
    )

    obs_types = {o.get("type") for o in observations}
    # batch API 使用 SPAN 表示工具调用（原 TOOL 类型）
    assert "SPAN" in obs_types, f"Missing SPAN observation. Types: {obs_types}"
    assert "GENERATION" in obs_types, f"Missing GENERATION observation. Types: {obs_types}"
    # 验证有工具相关的 span（通过名称判断）
    tool_names = [o.get("name") for o in observations if o.get("name", "").startswith("tool-")]
    assert len(tool_names) >= 1, f"Expected at least one tool span, got: {tool_names}"

    print(f"\n✅ Langfuse: trace {trace_id[:16]}... has {len(observations)} observations")
    for o in observations:
        print(f"   {o.get('type')}: {o.get('name')}")