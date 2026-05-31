"""T12-T14 + T_extra2 + T_extra4: CrewAI 适配层测试。"""

from unittest.mock import MagicMock

from crewai.hooks import (
    clear_all_global_hooks,
    get_before_llm_call_hooks,
    get_before_tool_call_hooks,
    get_after_tool_call_hooks,
)

from hook_framework.registry import EventType, HookContext, HookRegistry
from hook_framework.crew_adapter import CrewObservabilityAdapter


def _make_adapter():
    clear_all_global_hooks()
    registry = HookRegistry()
    events_received = []
    for et in EventType:
        registry.register(et, lambda ctx, _et=et: events_received.append(_et), name=f"test_{et.value}")
    adapter = CrewObservabilityAdapter(registry, session_id="test-session")
    return adapter, registry, events_received


# T12: BEFORE_TURN 轮次计数
def test_before_turn_counting():
    adapter, registry, events = _make_adapter()
    adapter.install_global_hooks()

    llm_hooks = get_before_llm_call_hooks()

    mock_ctx = MagicMock()
    mock_ctx.agent = MagicMock()
    mock_ctx.agent.role = "analyst"

    # 第1轮：第1次 LLM call → BEFORE_TURN + BEFORE_LLM
    for h in llm_hooks:
        h(mock_ctx)
    assert events.count(EventType.BEFORE_TURN) == 1
    assert events.count(EventType.BEFORE_LLM) == 1

    # 同轮第2次 LLM call → 只有 BEFORE_LLM
    for h in llm_hooks:
        h(mock_ctx)
    assert events.count(EventType.BEFORE_TURN) == 1
    assert events.count(EventType.BEFORE_LLM) == 2

    adapter.cleanup()


# T13: step_callback → AFTER_TURN
def test_step_callback_dispatches_after_turn():
    adapter, registry, events = _make_adapter()
    step_cb = adapter.make_step_callback()

    mock_step = MagicMock()
    mock_step.output = "some output"
    step_cb(mock_step)
    step_cb(mock_step)
    assert events.count(EventType.AFTER_TURN) == 2

    adapter.cleanup()


# T14: 轮次重置
def test_turn_reset_after_step():
    adapter, registry, events = _make_adapter()
    adapter.install_global_hooks()
    step_cb = adapter.make_step_callback()

    llm_hooks = get_before_llm_call_hooks()

    mock_ctx = MagicMock()
    mock_ctx.agent = MagicMock()
    mock_ctx.agent.role = "analyst"

    # Turn 1
    for h in llm_hooks:
        h(mock_ctx)
    step_cb(MagicMock(output="o1"))

    # Turn 2 (after reset)
    for h in llm_hooks:
        h(mock_ctx)
    assert events.count(EventType.BEFORE_TURN) == 2
    assert adapter._turn_count == 2

    adapter.cleanup()


# T_extra2: cleanup 清理全局 hooks
def test_cleanup_clears_global_hooks():
    adapter, registry, events = _make_adapter()
    adapter.install_global_hooks()

    assert len(get_before_llm_call_hooks()) > 0

    adapter.cleanup()
    assert EventType.SESSION_END in events
    assert len(get_before_llm_call_hooks()) == 0
    assert len(get_before_tool_call_hooks()) == 0
    assert len(get_after_tool_call_hooks()) == 0


# T_extra4: tool call 映射
def test_tool_call_mapping():
    adapter, registry, events = _make_adapter()
    adapter.install_global_hooks()

    before_hooks = get_before_tool_call_hooks()
    after_hooks = get_after_tool_call_hooks()

    mock_ctx = MagicMock()
    mock_ctx.tool_name = "web_search"
    mock_ctx.tool_input = {"query": "test"}

    for h in before_hooks:
        h(mock_ctx)
    for h in after_hooks:
        h(mock_ctx)

    assert EventType.BEFORE_TOOL_CALL in events
    assert EventType.AFTER_TOOL_CALL in events

    adapter.cleanup()