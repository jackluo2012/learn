"""成本围栏——实时累计成本，超预算时拒绝操作。"""

import json
import os
import sys

from hook_framework.registry import GuardrailDeny

MODEL_PRICES = {
    "qwen-plus": {"input": 0.80, "output": 2.00},
    "qwen-turbo": {"input": 0.30, "output": 0.60},
    "qwen-max": {"input": 2.40, "output": 9.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


class CostGuard:
    def __init__(self, budget_usd: float = 1.0, model: str = ""):
        env_budget = os.environ.get("COST_GUARD_BUDGET")
        resolved_budget = float(env_budget) if env_budget else budget_usd
        if resolved_budget < 0:
            raise ValueError(f"budget_usd must be non-negative, got {resolved_budget}")
        self._budget = resolved_budget
        self._model = model or os.environ.get("AGENT_MODEL", "qwen-plus")
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._estimated_cost = 0.0
        self._deny_count = 0

    def after_turn_handler(self, ctx):
        """AFTER_TURN: 累加 token，计算成本，超预算则 deny。"""
        self._total_input_tokens += ctx.input_tokens
        self._total_output_tokens += ctx.output_tokens
        self._estimated_cost = self._calculate_cost()
        self._emit_cost_update(ctx)

        if self._estimated_cost >= self._budget:
            self._deny_count += 1
            self._emit_deny(ctx)
            raise GuardrailDeny(
                f"Budget exceeded: ${self._estimated_cost:.4f} "
                f">= limit ${self._budget:.2f}"
            )

    def before_tool_handler(self, ctx):
        """BEFORE_TOOL_CALL: 检查预算，超出则拒绝。"""
        if self._estimated_cost >= self._budget:
            self._deny_count += 1
            self._emit_deny(ctx)
            raise GuardrailDeny(
                f"Budget exceeded: ${self._estimated_cost:.4f} "
                f">= limit ${self._budget:.2f}"
            )

    def _calculate_cost(self) -> float:
        prices = MODEL_PRICES.get(self._model, {"input": 1.0, "output": 3.0})
        return (
            self._total_input_tokens * prices["input"] / 1_000_000
            + self._total_output_tokens * prices["output"] / 1_000_000
        )

    def _emit_cost_update(self, ctx):
        record = {
            "level": "INFO",
            "guardrail": "cost_guard",
            "turn": ctx.turn_number,
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "estimated_cost_usd": round(self._estimated_cost, 6),
            "budget_usd": self._budget,
            "remaining_usd": round(self._budget - self._estimated_cost, 6),
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def _emit_deny(self, ctx):
        record = {
            "level": "CRITICAL",
            "guardrail": "cost_guard",
            "message": "Budget exceeded — blocking",
            "estimated_cost_usd": round(self._estimated_cost, 6),
            "budget_usd": self._budget,
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def get_metrics(self) -> dict:
        return {
            "model": self._model,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "estimated_cost_usd": round(self._estimated_cost, 6),
            "budget_usd": self._budget,
            "remaining_usd": round(
                max(0, self._budget - self._estimated_cost), 6
            ),
            "budget_utilization": round(
                self._estimated_cost / max(self._budget, 0.001), 2
            ),
            "deny_count": self._deny_count,
        }