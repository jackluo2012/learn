#!/usr/bin/env python3
"""
邮箱操作 CLI — Agent 通过 Bash 在沙盒中调用。

三态状态机（类比 AWS SQS Visibility Timeout）：
  send       → status: "unread"
  read       → status: "in_progress" + processing_since（原子操作，防重复取走）
  done       → status: "done"
  reset-stale→ in_progress 超时 → unread（崩溃恢复）

沙盒内调用示例：
  python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \\
      --mailboxes-dir /mnt/shared/mailboxes \\
      --from manager --to pm \\
      --type task_assign --subject "任务" --content "路径引用"
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from filelock import FileLock
except ImportError:
    import subprocess as _sp
    _sp.check_call([sys.executable, "-m", "pip", "install", "filelock", "-q"],
                   stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    from filelock import FileLock

STATUS_UNREAD      = "unread"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE        = "done"


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _save(path: Path, inbox: list[dict]) -> None:
    path.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_send(args: argparse.Namespace) -> None:
    mailboxes_dir = Path(args.mailboxes_dir)
    inbox_path = mailboxes_dir / f"{args.to}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")

    msg: dict = {
        "id":               f"msg-{uuid.uuid4().hex[:8]}",
        "from":             args.from_,
        "to":               args.to,
        "type":             args.type,
        "subject":          args.subject,
        "content":          args.content,
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "status":           STATUS_UNREAD,
        "processing_since": None,
    }

    with FileLock(str(lock_path)):
        inbox = _load(inbox_path)
        inbox.append(msg)
        _save(inbox_path, inbox)

    print(json.dumps({"errcode": 0, "data": {"msg_id": msg["id"]}}, ensure_ascii=False))


def cmd_read(args: argparse.Namespace) -> None:
    mailboxes_dir = Path(args.mailboxes_dir)
    inbox_path = mailboxes_dir / f"{args.role}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")
    unread: list[dict] = []

    with FileLock(str(lock_path)):
        inbox = _load(inbox_path)
        for msg in inbox:
            if msg.get("status") == STATUS_UNREAD:
                msg["status"]           = STATUS_IN_PROGRESS
                msg["processing_since"] = datetime.now(timezone.utc).isoformat()
                unread.append(dict(msg))
        _save(inbox_path, inbox)

    print(json.dumps(
        {"errcode": 0, "data": {"messages": unread}},
        ensure_ascii=False,
    ))


def cmd_done(args: argparse.Namespace) -> None:
    mailboxes_dir = Path(args.mailboxes_dir)
    inbox_path = mailboxes_dir / f"{args.role}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")
    found = False

    if not inbox_path.exists():
        print(json.dumps({
            "errcode": 1,
            "errmsg": f"邮箱文件不存在：{inbox_path}",
        }, ensure_ascii=False))
        return

    with FileLock(str(lock_path)):
        inbox = _load(inbox_path)
        for msg in inbox:
            if msg["id"] == args.msg_id and msg.get("status") == STATUS_IN_PROGRESS:
                msg["status"]           = STATUS_DONE
                msg["processing_since"] = None
                found = True
                break
        if found:
            _save(inbox_path, inbox)

    if found:
        print(json.dumps({"errcode": 0, "errmsg": "success"}, ensure_ascii=False))
    else:
        print(json.dumps({
            "errcode": 1,
            "errmsg": f"未找到 in_progress 状态的消息 {args.msg_id}",
        }, ensure_ascii=False))


def cmd_reset_stale(args: argparse.Namespace) -> None:
    mailboxes_dir = Path(args.mailboxes_dir)
    inbox_path = mailboxes_dir / f"{args.role}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")
    timeout_seconds = args.timeout_minutes * 60
    count = 0
    now   = datetime.now(timezone.utc)

    with FileLock(str(lock_path)):
        inbox = _load(inbox_path)
        for msg in inbox:
            if msg.get("status") == STATUS_IN_PROGRESS and msg.get("processing_since"):
                # 兼容带 +00:00 时区后缀的 ISO 格式（Python 3.11+ 原生支持）
                started = datetime.fromisoformat(
                    msg["processing_since"].replace("Z", "+00:00")
                )
                if (now - started).total_seconds() > timeout_seconds:
                    msg["status"]           = STATUS_UNREAD
                    msg["processing_since"] = None
                    count += 1
        _save(inbox_path, inbox)

    print(json.dumps({"errcode": 0, "data": {"reset_count": count}}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="邮箱操作 CLI（三态状态机）")
    sub = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = sub.add_parser("send", help="发送邮件")
    p_send.add_argument("--mailboxes-dir", required=True)
    p_send.add_argument("--from", dest="from_", required=True)
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--type", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--content", required=True)

    # read
    p_read = sub.add_parser("read", help="读取未读邮件（标记 in_progress）")
    p_read.add_argument("--mailboxes-dir", required=True)
    p_read.add_argument("--role", required=True)

    # done
    p_done = sub.add_parser("done", help="标记消息处理完成（in_progress → done）")
    p_done.add_argument("--mailboxes-dir", required=True)
    p_done.add_argument("--role", required=True)
    p_done.add_argument("--msg-id", dest="msg_id", required=True)

    # reset-stale
    p_reset = sub.add_parser("reset-stale", help="崩溃恢复：重置超时 in_progress → unread")
    p_reset.add_argument("--mailboxes-dir", required=True)
    p_reset.add_argument("--role", required=True)
    p_reset.add_argument("--timeout-minutes", type=int, default=15)

    args = parser.parse_args()
    {
        "send":        cmd_send,
        "read":        cmd_read,
        "done":        cmd_done,
        "reset-stale": cmd_reset_stale,
    }[args.command](args)


if __name__ == "__main__":
    main()
