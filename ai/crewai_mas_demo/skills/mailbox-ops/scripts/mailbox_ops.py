"""
mailbox-ops Skill 脚本
数字员工之间的邮箱通信：send_mail / read_inbox / mark_done / mark_done_all / reset_stale

三态状态机：unread → in_progress → done
  - send_mail:  写入 status="unread"
  - read_inbox: 取走 unread 消息，原子标记为 in_progress
  - mark_done:  将指定消息从 in_progress → done
  - mark_done_all: 将该角色所有 in_progress → done
  - reset_stale: 超时的 in_progress → unread（崩溃恢复）

在 AIO-Sandbox 中通过命令行调用：
  python3 mailbox_ops.py send_mail --mailbox-dir /mnt/shared/mailboxes --to pm --from manager ...
  python3 mailbox_ops.py read_inbox --mailbox-dir /mnt/shared/mailboxes --role pm
  python3 mailbox_ops.py mark_done --mailbox-dir /mnt/shared/mailboxes --role pm --msg-ids id1,id2
  python3 mailbox_ops.py mark_done_all --mailbox-dir /mnt/shared/mailboxes --role pm
  python3 mailbox_ops.py reset_stale --mailbox-dir /mnt/shared/mailboxes --role pm --timeout 900
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from filelock import FileLock, Timeout as FileLockTimeout
    _HAS_FILELOCK = True
except ImportError:
    _HAS_FILELOCK = False

_VALID_ROLES = {"manager", "pm", "dev", "qa"}
_LOCK_TIMEOUT = 10

STATUS_UNREAD = "unread"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"


def _ok(data: dict) -> None:
    print(json.dumps({"errcode": 0, "errmsg": "success", **data}, ensure_ascii=False))


def _err(code: int, msg: str) -> None:
    print(json.dumps({"errcode": code, "errmsg": msg}, ensure_ascii=False))
    sys.exit(1)


def _inbox_path(mailbox_dir: Path, role: str) -> Path:
    return mailbox_dir / f"{role}.json"


def _lock_path(inbox: Path) -> Path:
    return inbox.with_suffix(".lock")


def _read_file(inbox: Path) -> list[dict]:
    inbox.parent.mkdir(parents=True, exist_ok=True)
    if not inbox.exists():
        inbox.write_text("[]", encoding="utf-8")
        return []
    return json.loads(inbox.read_text(encoding="utf-8"))


def _write_file(inbox: Path, messages: list[dict]) -> None:
    inbox.write_text(json.dumps(messages, ensure_ascii=False, indent=2),
                     encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _with_lock(inbox: Path, fn):
    lock = _lock_path(inbox)
    if _HAS_FILELOCK:
        try:
            with FileLock(str(lock), timeout=_LOCK_TIMEOUT):
                return fn()
        except FileLockTimeout:
            _err(2, f"获取文件锁超时（>{_LOCK_TIMEOUT}s），请稍后重试")
    else:
        return fn()


def cmd_send_mail(args: argparse.Namespace) -> None:
    mailbox_dir = Path(args.mailbox_dir)
    to = args.to.lower()
    from_ = getattr(args, "from").lower()

    if to not in _VALID_ROLES:
        _err(1, f"无效的收件人角色 '{to}'，允许值：{_VALID_ROLES}")
    if from_ not in _VALID_ROLES:
        _err(1, f"无效的发件人角色 '{from_}'，允许值：{_VALID_ROLES}")

    inbox = _inbox_path(mailbox_dir, to)
    msg_id = str(uuid.uuid4())

    message = {
        "id": msg_id,
        "from": from_,
        "to": to,
        "type": args.type,
        "subject": args.subject,
        "content": args.content,
        "timestamp": _now_iso(),
        "status": STATUS_UNREAD,
        "processing_since": None,
    }

    def do():
        messages = _read_file(inbox)
        messages.append(message)
        _write_file(inbox, messages)

    _with_lock(inbox, do)
    _ok({"msg_id": msg_id})


def cmd_read_inbox(args: argparse.Namespace) -> None:
    mailbox_dir = Path(args.mailbox_dir)
    role = args.role.lower()

    if role not in _VALID_ROLES:
        _err(1, f"无效的角色 '{role}'，允许值：{_VALID_ROLES}")

    inbox = _inbox_path(mailbox_dir, role)
    result = {"messages": []}

    def do():
        messages = _read_file(inbox)
        unread = [dict(m) for m in messages if m.get("status", "unread") == STATUS_UNREAD]
        now = _now_iso()
        for m in messages:
            if m.get("status", "unread") == STATUS_UNREAD:
                m["status"] = STATUS_IN_PROGRESS
                m["processing_since"] = now
        _write_file(inbox, messages)
        result["messages"] = unread

    _with_lock(inbox, do)
    _ok(result)


def cmd_mark_done(args: argparse.Namespace) -> None:
    mailbox_dir = Path(args.mailbox_dir)
    role = args.role.lower()

    if role not in _VALID_ROLES:
        _err(1, f"无效的角色 '{role}'，允许值：{_VALID_ROLES}")

    msg_ids = set(args.msg_ids.split(","))
    inbox = _inbox_path(mailbox_dir, role)
    result = {"marked": 0}

    def do():
        messages = _read_file(inbox)
        count = 0
        for m in messages:
            if m.get("id") in msg_ids and m.get("status") == STATUS_IN_PROGRESS:
                m["status"] = STATUS_DONE
                count += 1
        _write_file(inbox, messages)
        result["marked"] = count

    _with_lock(inbox, do)
    _ok(result)


def cmd_mark_done_all(args: argparse.Namespace) -> None:
    mailbox_dir = Path(args.mailbox_dir)
    role = args.role.lower()

    if role not in _VALID_ROLES:
        _err(1, f"无效的角色 '{role}'，允许值：{_VALID_ROLES}")

    inbox = _inbox_path(mailbox_dir, role)
    result = {"marked": 0}

    def do():
        messages = _read_file(inbox)
        count = 0
        for m in messages:
            if m.get("status") == STATUS_IN_PROGRESS:
                m["status"] = STATUS_DONE
                count += 1
        _write_file(inbox, messages)
        result["marked"] = count

    _with_lock(inbox, do)
    _ok(result)


def cmd_reset_stale(args: argparse.Namespace) -> None:
    mailbox_dir = Path(args.mailbox_dir)
    role = args.role.lower()
    timeout = args.timeout

    if role not in _VALID_ROLES:
        _err(1, f"无效的角色 '{role}'，允许值：{_VALID_ROLES}")

    inbox = _inbox_path(mailbox_dir, role)
    result = {"reset": 0}
    now = datetime.now(timezone.utc)

    def do():
        messages = _read_file(inbox)
        count = 0
        for m in messages:
            if m.get("status") != STATUS_IN_PROGRESS:
                continue
            since_str = m.get("processing_since")
            if not since_str:
                m["status"] = STATUS_UNREAD
                m["processing_since"] = None
                count += 1
                continue
            since = datetime.fromisoformat(since_str)
            if (now - since).total_seconds() >= timeout:
                m["status"] = STATUS_UNREAD
                m["processing_since"] = None
                count += 1
        _write_file(inbox, messages)
        result["reset"] = count

    _with_lock(inbox, do)
    _ok(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="mailbox-ops: 数字员工邮箱操作（三态状态机）")
    sub = parser.add_subparsers(dest="command")

    p_send = sub.add_parser("send_mail", help="发送消息到指定角色的邮箱")
    p_send.add_argument("--mailbox-dir", required=True)
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--from", required=True, dest="from")
    p_send.add_argument("--type", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--content", required=True)

    p_read = sub.add_parser("read_inbox", help="读取 unread 消息（标记为 in_progress）")
    p_read.add_argument("--mailbox-dir", required=True)
    p_read.add_argument("--role", required=True)

    p_done = sub.add_parser("mark_done", help="将指定消息标记为 done")
    p_done.add_argument("--mailbox-dir", required=True)
    p_done.add_argument("--role", required=True)
    p_done.add_argument("--msg-ids", required=True, help="逗号分隔的消息 ID")

    p_done_all = sub.add_parser("mark_done_all", help="将所有 in_progress 消息标记为 done")
    p_done_all.add_argument("--mailbox-dir", required=True)
    p_done_all.add_argument("--role", required=True)

    p_reset = sub.add_parser("reset_stale", help="超时 in_progress → unread（崩溃恢复）")
    p_reset.add_argument("--mailbox-dir", required=True)
    p_reset.add_argument("--role", required=True)
    p_reset.add_argument("--timeout", type=int, default=900, help="超时秒数（默认 900）")

    args = parser.parse_args()

    cmds = {
        "send_mail": cmd_send_mail,
        "read_inbox": cmd_read_inbox,
        "mark_done": cmd_mark_done,
        "mark_done_all": cmd_mark_done_all,
        "reset_stale": cmd_reset_stale,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
