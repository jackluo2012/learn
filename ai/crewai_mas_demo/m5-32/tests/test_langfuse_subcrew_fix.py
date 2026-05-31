"""TDD: Sub-Crew Langfuse ContextVar + batch API 修复验证。

T-LF01: ContextVar 线程隔离（copy_context 行为）
T-LF02: subcrew_cleanup() 函数存在
T-LF03: _get_langfuse_parent_span_id() 函数存在
T-LF04: _reset_subcrew_state() 存在并正确重置状态
T-LF05: 无 OTel 死代码（_get_otel_span_id / _set_trace_attrs / start_observation / _span_stack_lock）
T-LF06: before_llm_handler 每次 LLM call 都创建 generation
T-LF07: before_llm_handler 从 ctx.metadata["model"] 读取模型名
T-LF08: flush_and_close 重置所有 ContextVar
T-SK01: skill_loader_tool._run() 使用 ctx.run() 传播 ContextVar
T-CA01: crew_adapter BEFORE_LLM 事件 metadata 包含 model 字段
"""

import concurrent.futures
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_M5L31_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_M5L31_DIR))

from hook_framework.registry import EventType, HookContext


# ── Helper ────────────────────────────────────────────────────────────────────

def _load_lt():
    """Load langfuse_trace, purging cached module to get a fresh import."""
    lt_dir = str(_M5L31_DIR / "shared_hooks")
    if lt_dir not in sys.path:
        sys.path.insert(0, lt_dir)
    for key in list(sys.modules.keys()):
        if "langfuse_trace" in key:
            del sys.modules[key]
    import langfuse_trace
    return langfuse_trace


def _ctx_with_trace(lt, session_id="s1", model="qwen3.6-max-preview"):
    """Seed ContextVars so _ensure_trace is a no-op (no real client needed)."""
    lt._trace_id_var.set(f"trace-{session_id}")
    lt._root_span_id_var.set("root-span-id")
    lt._gen_id_var.set("")
    lt._gen_count_var.set(0)
    lt._span_stack_var.set(())
    # point at a mock client so batch enqueue works
    lt._client = MagicMock()
    lt._batch_buffer.clear()
    return HookContext(
        event_type=EventType.BEFORE_LLM,
        session_id=session_id,
        turn_number=1,
        agent_id="test-agent",
        metadata={"model": model},
    )


# ── T-LF01: ContextVar 线程隔离 ──────────────────────────────────────────────

def test_contextvar_thread_isolation():
    """copy_context() 后子线程有独立副本，不污染主线程。"""
    import contextvars

    var: contextvars.ContextVar[str] = contextvars.ContextVar("_test_iso", default="")
    var.set("main-value")

    ctx = contextvars.copy_context()
    results: dict = {}

    def worker():
        results["before"] = var.get()
        var.set("child-value")
        results["after"] = var.get()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(ctx.run, worker).result()

    assert results["before"] == "main-value"
    assert results["after"] == "child-value"
    assert var.get() == "main-value"  # 主线程不受影响


# ── T-LF02: subcrew_cleanup() 存在 ───────────────────────────────────────────

def test_subcrew_cleanup_exists():
    lt = _load_lt()
    assert hasattr(lt, "subcrew_cleanup"), "subcrew_cleanup() 必须存在"
    assert callable(lt.subcrew_cleanup)


# ── T-LF03: _get_langfuse_parent_span_id() 存在 ──────────────────────────────

def test_get_langfuse_parent_span_id_exists():
    lt = _load_lt()
    assert hasattr(lt, "_get_langfuse_parent_span_id"), (
        "_get_langfuse_parent_span_id() 必须存在"
    )
    assert callable(lt._get_langfuse_parent_span_id)


# ── T-LF04: _reset_subcrew_state() 正确重置 ──────────────────────────────────

def test_reset_subcrew_state():
    lt = _load_lt()
    assert hasattr(lt, "_reset_subcrew_state"), "_reset_subcrew_state() 必须存在"

    lt._trace_id_var.set("trace-preserve")
    lt._root_span_id_var.set("old-root")
    lt._gen_id_var.set("old-gen")
    lt._gen_count_var.set(5)
    lt._span_stack_var.set((("span1", "tool1", 1, {}),))

    lt._reset_subcrew_state("new-parent-id")

    assert lt._trace_id_var.get() == "trace-preserve", "trace_id 必须保留"
    assert lt._root_span_id_var.get() == "new-parent-id", "root_span_id 必须设为 parent"
    assert lt._gen_id_var.get() == "", "gen_id 必须清空"
    assert lt._gen_count_var.get() == 0, "gen_count 必须归零"
    assert lt._span_stack_var.get() == (), "span_stack 必须清空"


# ── T-LF05: 无 OTel 死代码 ───────────────────────────────────────────────────

def test_no_otel_dead_code():
    content = (_M5L31_DIR / "shared_hooks" / "langfuse_trace.py").read_text()
    assert "_get_otel_span_id" not in content, (
        "_get_otel_span_id 是 OTel 死代码，必须删除"
    )
    assert "_set_trace_attrs" not in content, (
        "_set_trace_attrs 是 OTel 死代码，必须删除"
    )
    assert "start_observation" not in content, (
        "start_observation 是 OTel SDK 调用，必须改为 batch 注入"
    )
    assert "_span_stack_lock" not in content, (
        "_span_stack_lock 在 ContextVar 迁移后是死代码，必须删除"
    )


# ── T-LF06: before_llm_handler 创建 generation ───────────────────────────────

def test_before_llm_handler_creates_generation():
    lt = _load_lt()
    ctx = _ctx_with_trace(lt)

    lt.before_llm_handler(ctx)

    assert lt._gen_id_var.get() != "", "before_llm_handler 必须设置 _gen_id_var"
    gen_events = [
        e for e in lt._batch_buffer
        if getattr(e, "type", "") == "generation-create"
    ]
    assert len(gen_events) >= 1, (
        f"before_llm_handler 必须 enqueue generation-create 事件，"
        f"当前 buffer: {[getattr(e, 'type', '?') for e in lt._batch_buffer]}"
    )


# ── T-LF07: model 从 ctx.metadata 读取 ───────────────────────────────────────

def test_before_llm_handler_uses_metadata_model():
    lt = _load_lt()
    ctx = _ctx_with_trace(lt, model="qwen3.6-max-preview")

    lt.before_llm_handler(ctx)

    gen_events = [
        e for e in lt._batch_buffer
        if getattr(e, "type", "") == "generation-create"
    ]
    assert gen_events, "Expected generation-create event"
    model_val = gen_events[0].body.model
    assert model_val == "qwen3.6-max-preview", (
        f"model 必须来自 ctx.metadata，应为 'qwen3.6-max-preview'，实际: '{model_val}'"
    )


# ── T-LF08: flush_and_close 重置 ContextVar ──────────────────────────────────

def test_flush_and_close_resets_contextvars():
    lt = _load_lt()
    lt._trace_id_var.set("trace-cleanup")
    lt._root_span_id_var.set("root-id")
    lt._gen_id_var.set("gen-id")
    lt._gen_count_var.set(3)
    lt._span_stack_var.set((("s1", "t1", 1, {}),))
    lt._client = MagicMock()
    lt._batch_buffer.clear()

    ctx = HookContext(event_type=EventType.SESSION_END, session_id="s1")
    lt.flush_and_close(ctx)

    assert lt._trace_id_var.get() == "", "_trace_id_var 必须清空"
    assert lt._root_span_id_var.get() == "", "_root_span_id_var 必须清空"
    assert lt._gen_id_var.get() == "", "_gen_id_var 必须清空"
    assert lt._gen_count_var.get() == 0, "_gen_count_var 必须归零"
    assert lt._span_stack_var.get() == (), "_span_stack_var 必须清空"


# ── T-SK01: skill_loader_tool._run() 使用 ctx.run() ─────────────────────────

def test_skill_loader_run_uses_ctx_run():
    skill_file = _M5L31_DIR.parent / "tools" / "skill_loader_tool.py"
    content = skill_file.read_text()
    assert "copy_context" in content, (
        "_run() 必须调用 contextvars.copy_context() 以传播 ContextVar"
    )
    assert "ctx.run" in content, (
        "_run() 必须使用 ctx.run() 而非 pool.submit(asyncio.run, ...)"
    )


# ── T-CA01: crew_adapter BEFORE_LLM 包含 model ───────────────────────────────

def test_crew_adapter_before_llm_includes_model():
    from crewai.hooks import clear_all_global_hooks, get_before_llm_call_hooks
    from hook_framework.crew_adapter import CrewObservabilityAdapter
    from hook_framework.registry import HookRegistry

    clear_all_global_hooks()

    received: dict = {}

    def capture(ctx):
        if ctx.event_type == EventType.BEFORE_LLM:
            received["metadata"] = dict(ctx.metadata)

    registry = HookRegistry()
    registry.register(EventType.BEFORE_LLM, capture)

    adapter = CrewObservabilityAdapter(registry, session_id="test")
    adapter.install_global_hooks()

    mock_ctx = MagicMock()
    mock_ctx.agent = MagicMock(role="test-agent")
    mock_ctx.task = None
    mock_ctx.messages = []
    mock_llm = MagicMock()
    mock_llm.model = "qwen3.6-max-preview"
    mock_ctx.llm = mock_llm

    hooks = get_before_llm_call_hooks()
    assert hooks, "install_global_hooks() 必须注册 before_llm_call hook"
    for hook_fn in hooks:
        hook_fn(mock_ctx)

    clear_all_global_hooks()

    assert "metadata" in received, "BEFORE_LLM handler 未被调用"
    assert "model" in received["metadata"], (
        f"BEFORE_LLM metadata 必须包含 'model'，实际 keys: {list(received['metadata'].keys())}"
    )
    assert received["metadata"]["model"] == "qwen3.6-max-preview", (
        f"model 应为 'qwen3.6-max-preview'，实际: {received['metadata']['model']}"
    )