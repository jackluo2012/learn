"""T5-T8: RetryTracker 单元测试。"""

from hook_framework.registry import EventType, HookContext

from shared_hooks.retry_tracker import RetryTracker


def _tool_ctx(tool_name: str, success: bool):
    return HookContext(
        event_type=EventType.AFTER_TOOL_CALL,
        tool_name=tool_name,
        success=success,
        session_id="test",
    )


# T5: 连续失败计数正确
def test_consecutive_failure_count():
    rt = RetryTracker(max_retries=5)
    for _ in range(3):
        rt.after_tool_handler(_tool_ctx("search", False))
    metrics = rt.get_metrics()
    assert metrics["active_failures"]["search"] == 3


# T6: 成功重置计数
def test_success_resets_count():
    rt = RetryTracker()
    rt.after_tool_handler(_tool_ctx("search", False))
    rt.after_tool_handler(_tool_ctx("search", False))
    rt.after_tool_handler(_tool_ctx("search", True))
    metrics = rt.get_metrics()
    assert metrics["active_failures"]["search"] == 0


# T7: 重试成功率计算（第1次失败不算重试，第2、3次才算）
def test_retry_success_rate():
    rt = RetryTracker()
    rt.after_tool_handler(_tool_ctx("search", False))  # fail #1 (not a retry)
    rt.after_tool_handler(_tool_ctx("search", False))  # fail #2 (retry #1)
    rt.after_tool_handler(_tool_ctx("search", False))  # fail #3 (retry #2)
    rt.after_tool_handler(_tool_ctx("search", True))   # success (successful retry)
    metrics = rt.get_metrics()
    assert metrics["total_retries"] == 2
    assert metrics["successful_retries"] == 1
    assert metrics["retry_success_rate"] == 0.5


# T8: 不同工具独立计数
def test_independent_tool_counting():
    rt = RetryTracker()
    rt.after_tool_handler(_tool_ctx("tool_a", False))
    rt.after_tool_handler(_tool_ctx("tool_a", False))
    rt.after_tool_handler(_tool_ctx("tool_b", False))
    metrics = rt.get_metrics()
    assert metrics["active_failures"]["tool_a"] == 2
    assert metrics["active_failures"]["tool_b"] == 1


# T_extra: 无 tool_name 的事件被跳过
def test_empty_tool_name_ignored():
    rt = RetryTracker()
    rt.after_tool_handler(_tool_ctx("", False))
    metrics = rt.get_metrics()
    assert metrics["active_failures"] == {}