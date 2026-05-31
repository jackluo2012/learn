"""T9-T11: handler 单元测试。"""

import importlib.util
import json
import sys
from pathlib import Path

from hook_framework.registry import EventType, HookContext

# 直接 import handler 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared_hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "workspace" / "demo_agent" / "hooks"))


def _load_hook_module(name: str):
    module_path = Path(__file__).resolve().parent.parent / "shared_hooks" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# T9: LogHandler JSON schema 完整
def test_structured_log_json_schema(capsys):
    import structured_log

    ctx = HookContext(
        event_type=EventType.BEFORE_TURN,
        session_id="s1",
        turn_number=1,
        agent_id="analyst",
    )
    structured_log.before_turn_handler(ctx)
    captured = capsys.readouterr()
    record = json.loads(captured.err.strip())
    assert record["event"] == "before_turn"
    assert record["session_id"] == "s1"
    assert record["turn"] == 1
    assert record["agent_id"] == "analyst"


# T10: LogHandler 所有事件类型
def test_structured_log_all_events(capsys):
    import structured_log

    handlers = {
        EventType.BEFORE_TURN: structured_log.before_turn_handler,
        EventType.BEFORE_LLM: structured_log.before_llm_handler,
        EventType.BEFORE_TOOL_CALL: structured_log.before_tool_handler,
        EventType.AFTER_TOOL_CALL: structured_log.after_tool_handler,
        EventType.AFTER_TURN: structured_log.after_turn_handler,
    }
    for event_type, handler in handlers.items():
        handler(HookContext(event_type=event_type, session_id="s1"))

    captured = capsys.readouterr()
    lines = [l for l in captured.err.strip().split("\n") if l]
    assert len(lines) == 5
    for line in lines:
        record = json.loads(line)
        assert "event" in record
        assert "timestamp" in record


# T11: TaskAudit 写文件
def test_task_audit_writes_file(tmp_path, monkeypatch):
    import task_audit

    audit_file = tmp_path / "audit.log"
    monkeypatch.setattr(task_audit, "AUDIT_FILE", audit_file)

    ctx = HookContext(
        event_type=EventType.TASK_COMPLETE,
        session_id="s1",
        metadata={"raw_output": "some result text"},
    )
    task_audit.write_audit_entry(ctx)

    assert audit_file.exists()
    entry = json.loads(audit_file.read_text().strip())
    assert entry["session_id"] == "s1"
    assert entry["event"] == "task_complete"
    assert "some result" in entry["output_preview"]