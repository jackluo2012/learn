"""F8: 任务审计 handler（workspace）——写 JSON 审计条目到 workspace 目录。"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path(__file__).parent.parent / "audit.log"


def write_audit_entry(ctx):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": ctx.session_id,
        "event": "task_complete",
        "output_preview": ctx.metadata.get("raw_output", "")[:200],
    }
    try:
        with open(AUDIT_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[TaskAudit] write error: {e}", file=sys.stderr)
