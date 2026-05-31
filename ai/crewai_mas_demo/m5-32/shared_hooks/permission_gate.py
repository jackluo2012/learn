"""权限网关——Deny > Ask > Allow 三级工具权限控制。

设计参照：Claude Code permissions.ts 的 Deny > Ask > Allow 优先级模型。
所有决策都是确定性的配置驱动，零 LLM 依赖。
"""

from __future__ import annotations

import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from hook_framework.registry import GuardrailDeny

if TYPE_CHECKING:
    from .audit_logger import SecurityAuditLogger


class PermissionLevel(Enum):
    DENY = "deny"
    ASK = "ask"
    ALLOW = "allow"


class PermissionGate:
    def __init__(
        self,
        policy_path: Path | str | None = None,
        default: str = "ask",
        audit: SecurityAuditLogger | None = None,
    ):
        self._default = PermissionLevel(default)
        self._tool_permissions: dict[str, PermissionLevel] = {}
        self._decisions: list[dict] = []
        self._audit = audit

        env_policy = os.environ.get("SECURITY_POLICY_PATH")
        if env_policy:
            policy_path = Path(env_policy)
        elif isinstance(policy_path, str):
            policy_path = Path(policy_path) if policy_path else None
        if policy_path and policy_path.exists():
            self._load_policy(policy_path)

    def _load_policy(self, path: Path):
        with open(path) as f:
            config = yaml.safe_load(f)
        permissions = config.get("permissions", {})
        for tool_name, level in permissions.get("tools", {}).items():
            self._tool_permissions[tool_name.lower()] = PermissionLevel(level)
        default = permissions.get("default")
        if default:
            self._default = PermissionLevel(default)

    def before_tool_handler(self, ctx):
        """BEFORE_TOOL_CALL: 检查工具权限。"""
        tool = ctx.tool_name
        level = self._tool_permissions.get(tool.lower(), self._default)

        decision = {
            "tool": tool,
            "permission": level.value,
            "policy_source": "explicit" if tool in self._tool_permissions else "default",
        }
        self._decisions.append(decision)

        if level == PermissionLevel.DENY:
            self._emit_decision(ctx, level, blocked=True)
            if self._audit:
                self._audit.record_event("permission_deny", {
                    "tool": tool,
                    "policy_source": decision["policy_source"],
                })
            raise GuardrailDeny(
                f"Permission denied: tool '{tool}' is in DENY list"
            )

        elif level == PermissionLevel.ASK:
            self._emit_decision(ctx, level, blocked=False)
            if self._audit:
                self._audit.record_event("permission_ask", {"tool": tool})

        elif level == PermissionLevel.ALLOW:
            self._emit_decision(ctx, level, blocked=False)

    def _emit_decision(self, ctx, level: PermissionLevel, blocked: bool):
        record = {
            "level": "CRITICAL" if blocked else "INFO",
            "guardrail": "permission_gate",
            "tool": ctx.tool_name,
            "permission": level.value,
            "blocked": blocked,
            "session_id": ctx.session_id,
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def get_metrics(self) -> dict:
        deny_count = sum(1 for d in self._decisions if d["permission"] == "deny")
        ask_count = sum(1 for d in self._decisions if d["permission"] == "ask")
        allow_count = sum(1 for d in self._decisions if d["permission"] == "allow")
        return {
            "total_decisions": len(self._decisions),
            "deny_count": deny_count,
            "ask_count": ask_count,
            "allow_count": allow_count,
            "denied_tools": [
                d["tool"] for d in self._decisions if d["permission"] == "deny"
            ],
        }