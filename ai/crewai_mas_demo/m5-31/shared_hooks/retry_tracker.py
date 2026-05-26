"""重试追踪——记录工具失败/成功模式，输出度量指标。纯观测，不拒绝。"""

import json
import sys


class RetryTracker:
    def __init__(self, max_retries: int = 3):
        self._max_retries = max_retries
        self._failures: dict[str, int] = {}
        self._total_retries = 0
        self._successful_retries = 0

    def after_tool_handler(self, ctx):
        tool = ctx.tool_name
        if not tool:
            return

        if not ctx.success:
            prev = self._failures.get(tool, 0)
            self._failures[tool] = prev + 1
            if prev > 0:
                self._total_retries += 1
            if self._failures[tool] >= self._max_retries:
                self._emit_warning(tool)
        else:
            if self._failures.get(tool, 0) > 0:
                self._successful_retries += 1
            self._failures[tool] = 0

    def _emit_warning(self, tool: str):
        record = {
            "level": "WARNING",
            "guardrail": "retry_tracker",
            "message": f"Tool '{tool}' failed {self._failures[tool]} times consecutively",
            "tool": tool,
            "consecutive_failures": self._failures[tool],
            "max_retries": self._max_retries,
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def get_metrics(self) -> dict:
        return {
            "total_retries": self._total_retries,
            "successful_retries": self._successful_retries,
            "retry_success_rate": round(
                self._successful_retries / max(self._total_retries, 1), 2
            ),
            "active_failures": dict(self._failures),
        }