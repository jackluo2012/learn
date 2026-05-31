"""安全审计日志——汇总安全事件，写入可追溯的审计文件。"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class SecurityAuditLogger:
    def __init__(self, audit_file: Path | str | None = None):

        """
        初始化安全审计日志记录器
        
        Args:
            audit_file: 审计日志文件的路径，可以是Path对象、字符串路径或None
        """
        env_file = os.environ.get("SECURITY_AUDIT_FILE")  # 从环境变量获取审计文件路径
        if env_file:
            self._audit_file = Path(env_file)
        elif isinstance(audit_file, str):
            self._audit_file = Path(audit_file) if audit_file else None
        else:
            self._audit_file = audit_file
        self._events: list[dict] = []

    def record_event(self, event_type: str, details: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "security_event": event_type,
            **details,
        }
        self._events.append(entry)
        if self._audit_file:
            try:
                with open(self._audit_file, "a") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError as e:
                print(f"[SecurityAuditLogger] write error: {e}", file=sys.stderr)

    def session_end_handler(self, ctx):
        """SESSION_END: 输出安全审计摘要。"""
        summary = self.get_metrics()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "security_event": "session_summary",
            "session_id": ctx.session_id,
            **summary,
        }
        if self._audit_file:
            try:
                with open(self._audit_file, "a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except OSError as e:
                print(f"[SecurityAuditLogger] write error: {e}", file=sys.stderr)

    def get_metrics(self) -> dict:
        by_type: dict[str, int] = {}
        for e in self._events:
            t = e["security_event"]
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total_security_events": len(self._events),
            "events_by_type": by_type,
        }