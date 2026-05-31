"""T17-T19: SecurityAuditLogger 单元测试。"""

import json
from pathlib import Path

from hook_framework.registry import EventType, HookContext

from shared_hooks.audit_logger import SecurityAuditLogger


# T17: record_event 累计事件
def test_event_accumulation():
    logger = SecurityAuditLogger()
    logger.record_event("permission_deny", {"tool": "shell"})
    logger.record_event("sandbox_violation", {"type": "path_traversal"})
    logger.record_event("permission_deny", {"tool": "email"})

    m = logger.get_metrics()
    assert m["total_security_events"] == 3
    assert m["events_by_type"]["permission_deny"] == 2
    assert m["events_by_type"]["sandbox_violation"] == 1


# T18: 审计文件写入 JSONL
def test_audit_file_jsonl(tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    logger = SecurityAuditLogger(audit_file=audit_file)
    logger.record_event("permission_deny", {"tool": "shell"})
    logger.record_event("sandbox_violation", {"type": "path_traversal"})

    lines = audit_file.read_text().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "security_event" in entry


# T19: session_end_handler 输出摘要
def test_session_end_writes_summary(tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    logger = SecurityAuditLogger(audit_file=audit_file)
    logger.record_event("permission_deny", {"tool": "shell"})
    logger.record_event("permission_deny", {"tool": "email"})

    ctx = HookContext(
        event_type=EventType.SESSION_END,
        session_id="test-session",
    )
    logger.session_end_handler(ctx)

    lines = audit_file.read_text().strip().split("\n")
    assert len(lines) == 3
    summary = json.loads(lines[-1])
    assert summary["security_event"] == "session_summary"
    assert summary["session_id"] == "test-session"
    assert summary["total_security_events"] == 2