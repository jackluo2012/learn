#!/usr/bin/env python3
"""
邮箱操作 CLI — Agent 通过 Bash 在沙盒中调用。

第27课新增（相比第26课）：
  1. 单一接口约束：--to human 时 --from 必须是 manager，否则返回 errcode=1
  2. human.json 二态 Schema：用 read(false/true) 替代三态 status
     - Agent 邮箱（manager/pm）：status: unread → in_progress → done
     - Human 邮箱（human）：read: false → true（Human 不是 Agent，无 in_progress）
  3. 新增 check-human 子命令：检查 human.json 中指定类型的消息是否已被确认

Agent 邮箱三态状态机（类比 AWS SQS Visibility Timeout）：
  send       → status: "unread"
  read       → status: "in_progress" + processing_since（原子操作，防重复取走）
  done       → status: "done"
  reset-stale→ in_progress 超时 → unread（崩溃恢复）

沙盒内调用示例：
  # 发给 PM（Agent 邮箱，status 字段）
  python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \\
      --mailboxes-dir /mnt/shared/mailboxes \\
      --from manager --to pm \\
      --type task_assign --subject "任务" --content "路径引用"

  # 发给 Human（单一接口约束，read 字段）
  python3 /workspace/skills/mailbox/scripts/mailbox_cli.py send \\
      --mailboxes-dir /mnt/shared/mailboxes \\
      --from manager --to human \\
      --type needs_confirm --subject "需求待确认" --content "/mnt/shared/needs/requirements.md"

  # 检查 Human 是否已确认
  python3 /workspace/skills/mailbox/scripts/mailbox_cli.py check-human \\
      --mailboxes-dir /mnt/shared/mailboxes \\
      --type needs_confirm
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


def _is_human_inbox(to: str) -> bool:
    return to == "human"


def cmd_send(args: argparse.Namespace) -> None:
    mailboxes_dir = Path(args.mailboxes_dir)
    inbox_path = mailboxes_dir / f"{args.to}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")

    # ── 单一接口约束：只有 manager 可以给 human 发消息 ──────────────────────
    if _is_human_inbox(args.to) and args.from_ != "manager":
        print(json.dumps({
            "errcode": 1,
            "errmsg": (
                f"单一接口约束：只有 manager 可以给 human 发消息，"
                f"当前发件人：{args.from_}"
            ),
        }, ensure_ascii=False))
        sys.exit(1)

    # ── 构造消息（human.json 用二态 read 字段，其他用三态 status）────────────
    if _is_human_inbox(args.to):
        msg: dict = {
            "id":        f"msg-{uuid.uuid4().hex[:8]}",
            "from":      args.from_,
            "to":        args.to,
            "type":      args.type,
            "subject":   args.subject,
            "content":   args.content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read":      False,                # 二态：Human 读后改为 True
        }
    else:
        msg = {
            "id":               f"msg-{uuid.uuid4().hex[:8]}",
            "from":             args.from_,
            "to":               args.to,
            "type":             args.type,
            "subject":          args.subject,
            "content":          args.content,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "status":           STATUS_UNREAD,  # 三态：Agent 邮箱
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
                started = datetime.fromisoformat(
                    msg["processing_since"].replace("Z", "+00:00")
                )
                if (now - started).total_seconds() > timeout_seconds:
                    msg["status"]           = STATUS_UNREAD
                    msg["processing_since"] = None
                    count += 1
        _save(inbox_path, inbox)

    print(json.dumps({"errcode": 0, "data": {"reset_count": count}}, ensure_ascii=False))


def cmd_check_human(args: argparse.Namespace) -> None:
    """
    检查 human.json 中指定类型的消息是否已被 Human 确认（read: true）。

    教学用途：Manager 在下一轮运行时调用此命令，判断是否可以继续推进。
    """
    mailboxes_dir = Path(args.mailboxes_dir)
    human_inbox = mailboxes_dir / "human.json"
    lock_path   = human_inbox.with_suffix(".json.lock")

    if not human_inbox.exists():
        print(json.dumps({
            "errcode": 0,
            "data": {"confirmed": False, "reason": "human.json 不存在"},
        }, ensure_ascii=False))
        return

    with FileLock(str(lock_path)):
        inbox = _load(human_inbox)

    # 找到最新的指定类型消息，检查是否 read=True 且 rejected 不为 True
    matches = [
        m for m in inbox
        if m.get("type") == args.type
    ]

    if not matches:
        print(json.dumps({
            "errcode": 0,
            "data": {
                "confirmed": False,
                "reason": f"human.json 中没有 type={args.type} 的消息",
            },
        }, ensure_ascii=False))
        return

    latest = matches[-1]
    if latest.get("read") and not latest.get("rejected"):
        print(json.dumps({
            "errcode": 0,
            "data": {
                "confirmed": True,
                "msg_id": latest.get("id"),
                "human_feedback": latest.get("human_feedback"),
            },
        }, ensure_ascii=False))
    elif latest.get("rejected"):
        print(json.dumps({
            "errcode": 0,
            "data": {
                "confirmed": False,
                "rejected": True,
                "msg_id": latest.get("id"),
                "human_feedback": latest.get("human_feedback"),
                "reason": "Human 拒绝了请求",
            },
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "errcode": 0,
            "data": {
                "confirmed": False,
                "msg_id": latest.get("id"),
                "reason": "Human 尚未确认",
            },
        }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="邮箱操作 CLI（第27课·单一接口约束 + human.json 二态）")
    sub = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = sub.add_parser("send", help="发送邮件（发给 human 时只有 manager 可以）")
    p_send.add_argument("--mailboxes-dir", required=True)
    p_send.add_argument("--from", dest="from_", required=True)
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--type", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--content", required=True)

    # read
    p_read = sub.add_parser("read", help="读取未读邮件（标记 in_progress，仅 Agent 邮箱）")
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

    # check-human（第27课新增）
    p_check = sub.add_parser(
        "check-human",
        help="检查 human.json 中指定类型的消息是否已被 Human 确认（第27课新增）",
    )
    p_check.add_argument("--mailboxes-dir", required=True)
    p_check.add_argument("--type", required=True, help="消息类型（如 needs_confirm / sop_confirm）")

    args = parser.parse_args()
    {
        "send":          cmd_send,
        "read":          cmd_read,
        "done":          cmd_done,
        "reset-stale":   cmd_reset_stale,
        "check-human":   cmd_check_human,
    }[args.command](args)


if __name__ == "__main__":
    main()
