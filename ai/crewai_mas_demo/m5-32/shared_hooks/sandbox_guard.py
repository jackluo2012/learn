"""沙箱输入消毒——确定性规则检查，零 LLM 依赖。

设计参照：Claude Code cyberRiskInstruction.ts 的四层确定性防御。
本模块实现其中三层：路径归一化 / 危险命令检测 / 环境变量引用检测。

【修订说明】
误报根因：shell injection 正则 `[;&|`]` 包含 `|`，而 markdown 表格普遍含 `|`。
错误修法：按工具名豁免（mcp_/sandbox_）—— 攻击者可借用这类工具绕过检测。
正确修法：按字段语义分层检测。

字段分两类：
- 命令类（command / query / cmd / args / code / shell）：三项全检，含 shell injection
- 内容类（其余字段，如 content / body / text）：只检路径穿越 + 危险命令

这样 markdown 写入（content 字段含 |）不触发误报，
而命令注入（command 字段含 ; | $()）仍被拦截。
"""

from __future__ import annotations

import json
import os
import re
import sys
from urllib.parse import unquote
from typing import TYPE_CHECKING

from hook_framework.registry import GuardrailDeny

if TYPE_CHECKING:
    from .audit_logger import SecurityAuditLogger

_PATH_TRAVERSAL = re.compile(r"\.\.[/\\]")
_ENV_VAR_REF = re.compile(r"\$\{?\w+\}?")
_DANGEROUS_COMMANDS = re.compile(
    r"\b(rm\s+-rf|sudo|chmod\s+777|curl\s.*\|.*sh|wget\s.*\|.*sh|eval|exec|dd\s+if=|mkfs|shred)\b",
    re.IGNORECASE,
)
# 不含 () 和 $：括号在自然语言常见，$ 由 _ENV_VAR_REF 单独处理
_SHELL_INJECTION = re.compile(r"[;&|`]|\$\(")

# 命令类字段名：这些字段的值会被当作命令/查询执行，需做 shell injection 全检
_CMD_FIELD_NAMES = frozenset({"command", "query", "cmd", "args", "code", "shell", "script"})


class SandboxGuard:
    def __init__(
        self,
        workspace_root: str = "",
        audit: SecurityAuditLogger | None = None,
    ):
        self._workspace_root = os.path.abspath(workspace_root) if workspace_root else ""
        self._violations: list[dict] = []
        self._audit = audit

    def before_tool_handler(self, ctx):
        """BEFORE_TOOL_CALL: 按字段语义分层消毒。

        命令类字段（command/query/cmd/args/code/shell）：三项全检。
        内容类字段（content/body/text 等）：只检路径穿越 + 危险命令。
        """
        if not ctx.tool_input:
            return

        for field, value in ctx.tool_input.items():
            text = unquote(str(value))
            if not text:
                continue

            # 路径穿越：所有字段都检（content 里藏 ../ 同样危险）
            if _PATH_TRAVERSAL.search(text):
                self._record_violation(ctx, "path_traversal", text)
                raise GuardrailDeny(
                    f"Path traversal blocked in tool '{ctx.tool_name}' "
                    f"field '{field}': input contains '../'"
                )

            # 危险命令：所有字段都检
            match = _DANGEROUS_COMMANDS.search(text)
            if match:
                self._record_violation(ctx, "dangerous_command", text)
                raise GuardrailDeny(
                    f"Dangerous command blocked in tool '{ctx.tool_name}' "
                    f"field '{field}': '{match.group()}'"
                )

            # Shell injection：仅检命令类字段，内容类字段跳过
            if field.lower() in _CMD_FIELD_NAMES and _SHELL_INJECTION.search(text):
                self._record_violation(ctx, "shell_injection", text)
                raise GuardrailDeny(
                    f"Shell injection blocked in tool '{ctx.tool_name}' "
                    f"field '{field}'"
                )

            if _ENV_VAR_REF.search(text):
                self._record_warning(ctx, "env_var_reference", text)

    def _record_violation(self, ctx, violation_type: str, input_preview: str):
        violation = {
            "type": violation_type,
            "tool": ctx.tool_name,
            "input_preview": input_preview[:200],
            "session_id": ctx.session_id,
        }
        self._violations.append(violation)
        record = {
            "level": "CRITICAL",
            "guardrail": "sandbox_guard",
            "violation": violation_type,
            "tool": ctx.tool_name,
            "blocked": True,
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)
        if self._audit:
            self._audit.record_event(f"sandbox_{violation_type}", {
                "tool": ctx.tool_name,
                "input_preview": input_preview[:100],
            })

    def _record_warning(self, ctx, warning_type: str, input_preview: str):
        record = {
            "level": "WARNING",
            "guardrail": "sandbox_guard",
            "warning": warning_type,
            "tool": ctx.tool_name,
            "input_preview": input_preview[:100],
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def get_metrics(self) -> dict:
        by_type: dict[str, int] = {}
        for v in self._violations:
            by_type[v["type"]] = by_type.get(v["type"], 0) + 1
        return {
            "total_violations": len(self._violations),
            "violations_by_type": by_type,
            "blocked_tools": list({v["tool"] for v in self._violations}),
        }