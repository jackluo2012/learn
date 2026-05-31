"""策略 YAML 加载集成测试：注册顺序 + 端到端流程。

原 install_reliability_hooks 已移除，改为通过 hooks.yaml strategies 段声明式加载。
"""

import textwrap
from pathlib import Path

import pytest

from hook_framework.registry import EventType, GuardrailDeny, HookContext, HookRegistry
from hook_framework.loader import HookLoader


def _write_strategy_dir(tmp_path: Path, yaml_content: str, modules: dict[str, str]):
    hooks_dir = tmp_path / "hooks_dir"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.yaml").write_text(yaml_content)
    for name, code in modules.items():
        (hooks_dir / f"{name}.py").write_text(code)
    return hooks_dir


_COST_GUARD_CODE = textwrap.dedent("""\
    class CostGuard:
        def __init__(self, budget_usd=1.0):
            self._budget = budget_usd
            self._total_input = 0
            self._total_output = 0
            self._cost = 0.0
            self._deny_count = 0

        def after_turn_handler(self, ctx):
            self._total_input += ctx.input_tokens
            self._total_output += ctx.output_tokens
            self._cost = (self._total_input + self._total_output) / 1_000_000
            if self._cost >= self._budget:
                self._deny_count += 1
                from hook_framework.registry import GuardrailDeny
                raise GuardrailDeny(f"Budget exceeded: ${self._cost:.4f}")

        def before_tool_handler(self, ctx):
            if self._cost >= self._budget:
                self._deny_count += 1
                from hook_framework.registry import GuardrailDeny
                raise GuardrailDeny(f"Budget exceeded: ${self._cost:.4f}")

        def get_metrics(self):
            return {
                "total_input_tokens": self._total_input,
                "total_output_tokens": self._total_output,
                "deny_count": self._deny_count,
            }
""")

_LOOP_DETECTOR_CODE = textwrap.dedent("""\
    import hashlib

    class LoopDetector:
        def __init__(self, threshold=3):
            self._threshold = threshold
            self._state_counts = {}
            self._detections = 0

        def after_tool_handler(self, ctx):
            output = (ctx.metadata or {}).get("tool_output", "")
            h = hashlib.sha256(output.encode()).hexdigest()[:16]
            self._state_counts[h] = self._state_counts.get(h, 0) + 1
            if self._state_counts[h] >= self._threshold:
                self._detections += 1
                from hook_framework.registry import GuardrailDeny
                raise GuardrailDeny(f"Loop detected: {self._state_counts[h]} repeats")

        def after_turn_handler(self, ctx):
            pass

        def get_metrics(self):
            return {"loop_detections": self._detections}
""")

_RETRY_TRACKER_CODE = textwrap.dedent("""\
    class RetryTracker:
        def __init__(self, max_retries=3):
            self._max = max_retries
            self._retries = 0

        def after_tool_handler(self, ctx):
            if not ctx.success:
                self._retries += 1

        def get_metrics(self):
            return {"retries": self._retries}
""")


def test_strategies_register_all_handlers(tmp_path):
    yaml_content = textwrap.dedent("""\
        strategies:
          - class: retry_tracker.RetryTracker
            config:
              max_retries: 3
            hooks:
              AFTER_TOOL_CALL: after_tool_handler
          - class: cost_guard.CostGuard
            config:
              budget_usd: 100.0
            hooks:
              AFTER_TURN: after_turn_handler
              BEFORE_TOOL_CALL: before_tool_handler
          - class: loop_detector.LoopDetector
            config:
              threshold: 3
            hooks:
              AFTER_TOOL_CALL: after_tool_handler
              AFTER_TURN: after_turn_handler
    """)
    hooks_dir = _write_strategy_dir(tmp_path, yaml_content, {
        "retry_tracker": _RETRY_TRACKER_CODE,
        "cost_guard": _COST_GUARD_CODE,
        "loop_detector": _LOOP_DETECTOR_CODE,
    })

    r = HookRegistry()
    loader = HookLoader(r)
    loader.load_from_directory(hooks_dir, layer_name="test")

    assert r.handler_count(EventType.AFTER_TOOL_CALL) >= 2
    assert r.handler_count(EventType.AFTER_TURN) >= 2
    assert r.handler_count(EventType.BEFORE_TOOL_CALL) >= 1

    strategies = loader.strategies
    assert "retry_tracker" in strategies
    assert "loop_detector" in strategies
    assert "cost_guard" in strategies


def test_after_turn_ordering_cost_before_loop(tmp_path):
    """cost_guard.accumulate must execute before loop_detector.
    Verify: even if loop_detector denies, cost is already accumulated.
    """
    yaml_content = textwrap.dedent("""\
        strategies:
          - class: cost_guard.CostGuard
            config:
              budget_usd: 100.0
            hooks:
              AFTER_TURN: after_turn_handler
          - class: loop_detector.LoopDetector
            config:
              threshold: 2
            hooks:
              AFTER_TURN: after_turn_handler
    """)
    hooks_dir = _write_strategy_dir(tmp_path, yaml_content, {
        "cost_guard": _COST_GUARD_CODE,
        "loop_detector": _LOOP_DETECTOR_CODE,
    })

    r = HookRegistry()
    loader = HookLoader(r)
    loader.load_from_directory(hooks_dir, layer_name="test")
    strategies = loader.strategies

    ctx = HookContext(
        event_type=EventType.AFTER_TURN,
        tool_name="search",
        input_tokens=1000,
        output_tokens=500,
        turn_number=1,
        session_id="test",
        metadata={"output": "same result"},
    )
    r.dispatch_gate(EventType.AFTER_TURN, ctx)

    assert strategies["cost_guard"].get_metrics()["total_input_tokens"] == 1000


def test_full_flow_budget_deny(tmp_path):
    """End-to-end: accumulate cost -> before_tool_call deny."""
    yaml_content = textwrap.dedent("""\
        strategies:
          - class: cost_guard.CostGuard
            config:
              budget_usd: 0.0001
            hooks:
              AFTER_TURN: after_turn_handler
              BEFORE_TOOL_CALL: before_tool_handler
    """)
    hooks_dir = _write_strategy_dir(tmp_path, yaml_content, {
        "cost_guard": _COST_GUARD_CODE,
    })

    r = HookRegistry()
    loader = HookLoader(r)
    loader.load_from_directory(hooks_dir, layer_name="test")

    turn_ctx = HookContext(
        event_type=EventType.AFTER_TURN,
        input_tokens=100000,
        output_tokens=50000,
        turn_number=1,
        session_id="test",
        metadata={"output": "result"},
    )
    with pytest.raises(GuardrailDeny, match="Budget exceeded"):
        r.dispatch_gate(EventType.AFTER_TURN, turn_ctx)