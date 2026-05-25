"""T1-T5 + T_extra1: HookRegistry 单元测试。"""

from unittest.mock import MagicMock

from hook_framework.registry import EventType, HookContext, HookRegistry


def _ctx(event_type=EventType.BEFORE_TURN):
    return HookContext(event_type=event_type, session_id="test")


# T1: 注册 + 分发
def test_register_and_dispatch():
    r = HookRegistry()
    handler = MagicMock()
    r.register(EventType.BEFORE_TURN, handler)
    r.dispatch(EventType.BEFORE_TURN, _ctx())
    handler.assert_called_once()


# T2: 同事件多 handler
def test_multiple_handlers_same_event():
    r = HookRegistry()
    h1, h2, h3 = MagicMock(), MagicMock(), MagicMock()
    r.register(EventType.BEFORE_LLM, h1)
    r.register(EventType.BEFORE_LLM, h2)
    r.register(EventType.BEFORE_LLM, h3)
    r.dispatch(EventType.BEFORE_LLM, _ctx(EventType.BEFORE_LLM))
    h1.assert_called_once()
    h2.assert_called_once()
    h3.assert_called_once()


# T3: 无 handler 不报错
def test_dispatch_no_handler():
    r = HookRegistry()
    r.dispatch(EventType.SESSION_END, _ctx(EventType.SESSION_END))


# T4: summary 正确
def test_summary():
    r = HookRegistry()
    r.register(EventType.BEFORE_LLM, lambda c: None, name="h1")
    r.register(EventType.BEFORE_LLM, lambda c: None, name="h2")
    s = r.summary()
    assert "before_llm" in s
    assert len(s["before_llm"]) == 2
    assert "h1" in s["before_llm"]


# T5: handler_count
def test_handler_count():
    r = HookRegistry()
    r.register(EventType.AFTER_TURN, lambda c: None)
    r.register(EventType.AFTER_TURN, lambda c: None)
    r.register(EventType.AFTER_TURN, lambda c: None)
    assert r.handler_count(EventType.AFTER_TURN) == 3
    assert r.handler_count(EventType.BEFORE_LLM) == 0


# T_extra1: handler 异常不中断后续 handler
def test_dispatch_handler_exception_does_not_break_others():
    r = HookRegistry()
    good_before = MagicMock()
    good_after = MagicMock()

    def bad_handler(ctx):
        raise RuntimeError("boom")

    r.register(EventType.BEFORE_TURN, good_before)
    r.register(EventType.BEFORE_TURN, bad_handler)
    r.register(EventType.BEFORE_TURN, good_after)

    r.dispatch(EventType.BEFORE_TURN, _ctx())
    good_before.assert_called_once()
    good_after.assert_called_once()