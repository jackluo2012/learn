"""
第27课：Human as 甲方 — Human 端命令行工具（v3 核心新增）

与 v2 的 wait_for_human() 对比：
  v2：wait_for_human() 在 run_demo.py 中阻塞，Manager 进程被锁住
  v3：human_cli.py 独立运行，Manager 完成当前能做的事就退出，Human 异步回复

使用方式：
  python human_cli.py           # 交互式模式（推荐）
  python human_cli.py check     # 只检查有无新消息
  python human_cli.py respond <msg_id> y              # 确认
  python human_cli.py respond <msg_id> n "修改意见"   # 拒绝+反馈

设计原则：
  - human.json 使用二态（read: false/true），而非三态
    Human 不是 Agent，不需要 in_progress 状态
  - FileLock 保护读-改-写（与 mailbox_cli.py 共享锁路径）
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from filelock import FileLock
except ImportError:
    print("❌ 缺少依赖，请运行：pip install filelock")
    sys.exit(1)

_M4L27_DIR    = Path(__file__).resolve().parent
MAILBOXES_DIR = _M4L27_DIR / "workspace" / "shared" / "mailboxes"
HUMAN_INBOX   = MAILBOXES_DIR / "human.json"
LOCK_PATH     = MAILBOXES_DIR / "human.json.lock"

# 消息类型中文说明
TYPE_LABELS: dict[str, str] = {
    "needs_confirm":      "需求文档确认",
    "sop_draft_confirm":  "SOP 草稿确认",
    "sop_confirm":        "SOP 选择确认",
    "checkpoint_request": "阶段性交付物审核",
    "error_alert":        "异常上报",
}

def _load_inbox() -> list[dict]:
    if not HUMAN_INBOX.exists():
        return []
    with FileLock(str(LOCK_PATH)):
        return json.loads(HUMAN_INBOX.read_text(encoding="utf-8"))

def check_messages() -> list[dict]:
    """检查 human.json 中是否有未读消息，返回未读列表。"""
    inbox = _load_inbox()
    return [m for m in inbox if not m.get("read", False)]

def respond(msg_id: str, confirmed: bool, feedback: Optional[str] = None) -> bool:
    """
    Human 对消息的回复（FileLock 保护的原子读-改-写）。

    Args:
        msg_id:    要回复的消息 ID
        confirmed: True 表示确认（y），False 表示拒绝（n）
        feedback:  拒绝时的修改意见（可选）

    Returns:
        True 表示找到并更新了消息，False 表示消息不存在
    """
    if not HUMAN_INBOX.exists():
        return False

    with FileLock(str(LOCK_PATH)):
        inbox = json.loads(HUMAN_INBOX.read_text(encoding="utf-8"))
        found = False
        for msg in inbox:
            if msg.get("id") == msg_id:
                msg["read"] = True
                if not confirmed:
                    msg["rejected"] = True
                    if feedback:
                        msg["human_feedback"] = feedback
                found = True
                break
        if found:
            HUMAN_INBOX.write_text(
                json.dumps(inbox, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    return found


def _print_message(msg: dict) -> None:
    """格式化打印单条消息。"""
    type_label = TYPE_LABELS.get(msg.get("type", ""), msg.get("type", ""))
    print(f"\n{'─'*50}")
    print(f"  消息 ID：{msg.get('id', '')}")
    print(f"  类型：{type_label}（{msg.get('type', '')}）")
    print(f"  来自：{msg.get('from', 'manager')}")
    print(f"  主题：{msg.get('subject', '')}")
    print(f"  内容：{msg.get('content', '')}")
    print(f"  时间：{msg.get('timestamp', '')}")
    print(f"{'─'*50}")


def interactive() -> None:
    """
    交互式模式：循环检查消息，等待 Human 逐条回复。

    与 v2 wait_for_human() 的关键区别：
      v2 中 Manager 进程被 input() 锁住
      v3 中 Manager 已退出，Human 在这里独立操作
    """
    print(f"\n{'='*60}")
    print("  Human 端 — 消息中心（第27课 v3 异步模式）")
    print(f"{'='*60}")
    print(f"  监听：{HUMAN_INBOX}")
    print("  按 Ctrl+C 退出")
    print(f"{'='*60}\n")

    while True:
        unread = check_messages()
        if not unread:
            print("  📭 没有新消息，5秒后重新检查... (Ctrl+C 退出)", end="\r")
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n\n  已退出 Human 端")
                break
            continue

        print(f"\n  📬 收到 {len(unread)} 条新消息：")
        for msg in unread:
            _print_message(msg)
            try:
                choice = input("  你的决定 (y/n)：").strip().lower()
            except KeyboardInterrupt:
                print("\n\n  已退出 Human 端")
                return

            if choice == "y":
                ok = respond(msg["id"], confirmed=True)
                if ok:
                    print(f"  ✅ 已确认：{msg.get('subject', '')}")
            else:
                try:
                    feedback_input = input(
                        "  修改意见（直接回车跳过）："
                    ).strip()
                except KeyboardInterrupt:
                    print("\n\n  已退出 Human 端")
                    return
                feedback = feedback_input if feedback_input else None
                ok = respond(msg["id"], confirmed=False, feedback=feedback)
                if ok:
                    label = f"（反馈：{feedback}）" if feedback else ""
                    print(f"  ↩️  已拒绝：{msg.get('subject', '')} {label}")

def cmd_check() -> None:
    """检查命令：打印所有未读消息摘要。"""
    unread = check_messages()
    if not unread:
        print(json.dumps({"status": "no_unread", "count": 0}, ensure_ascii=False))
        return
    result = [
        {
            "id": m.get("id"),
            "type": m.get("type"),
            "subject": m.get("subject"),
        }
        for m in unread
    ]
    print(json.dumps({"status": "has_unread", "count": len(unread), "messages": result},
                     ensure_ascii=False, indent=2))

def cmd_respond(msg_id: str, confirmed: bool, feedback: Optional[str]) -> None:
    """回复命令：对指定消息确认或拒绝。"""
    ok = respond(msg_id, confirmed, feedback)
    if ok:
        print(json.dumps({
            "errcode": 0,
            "msg_id": msg_id,
            "confirmed": confirmed,
            "feedback": feedback,
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "errcode": 1,
            "errmsg": f"消息 {msg_id} 不存在或已被处理",
        }, ensure_ascii=False))
        sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Human 端消息工具 — 读写 human.json（第27课 v3）",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="检查未读消息（JSON 输出，适合脚本调用）")

    p_respond = sub.add_parser("respond", help="对消息回复确认/拒绝")
    p_respond.add_argument("msg_id", help="消息 ID")
    p_respond.add_argument("decision", choices=["y", "n"], help="y=确认 / n=拒绝")
    p_respond.add_argument("feedback", nargs="?", default=None, help="拒绝时的修改意见（可选）")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check()
    elif args.command == "respond":
        cmd_respond(
            msg_id=args.msg_id,
            confirmed=(args.decision == "y"),
            feedback=args.feedback,
        )
    else:
        # 无子命令 → 交互式模式
        interactive()

if __name__ == "__main__":
    main()