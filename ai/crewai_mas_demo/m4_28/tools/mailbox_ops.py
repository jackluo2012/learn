"""
第28课·数字员工的自我进化（v6）
tools/mailbox_ops.py

v6 变更（基于第27课）：
  + send_mail 新增 L1 自动写入（to="human" 时，对调用方透明）
  + 新增 project_id 可选字段（语义 task 标识，由 init_project Skill 创建）
  + type 白名单校验：只允许已知消息类型，防止拼写错误导致路由丢失
  + 新增复盘相关类型：retro_trigger / retro_proposals_ready / retro_proposal /
    retro_decision / retro_approved / retro_applied / apply_locked / retro_stuck
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

_VALID_TO_ROLES   = {"manager", "pm", "human"}
_VALID_FROM_ROLES = {"manager", "pm"}

_VALID_TYPES = {
    # 业务流程
    "task_assign",
    "task_result",
    "checkpoint_request",
    "checkpoint_approved",
    "checkpoint_rejected",
    "weekly_report",
    # 复盘流程（v6）
    "retro_trigger",
    "team_retro_trigger",
    "retro_proposals_ready",
    "retro_proposal",
    "retro_decision",
    "retro_approved",
    "retro_applied",
    "apply_locked",
    "retro_stuck",
}


def _inbox_path(mailbox_dir: Path, role: str) -> Path:
    if role not in _VALID_TO_ROLES:
        raise ValueError(f"未知收件角色 '{role}'，允许值：{_VALID_TO_ROLES}")
    return mailbox_dir / f"{role}.json"


def _lock_path(inbox: Path) -> Path:
    return inbox.with_suffix(".lock")


def _read_inbox_file(inbox: Path) -> list[dict]:
    inbox.parent.mkdir(parents=True, exist_ok=True)
    if not inbox.exists():
        inbox.write_text("[]", encoding="utf-8")
        return []
    return json.loads(inbox.read_text(encoding="utf-8"))


def _write_l1_log(mailbox_dir: Path, message: dict) -> None:
    """
    将发往 human.json 的消息同步写一份到 L1 日志目录。

    教学要点（对应第28课 P2）：
      L1 日志记录所有进出 human.json 的消息，尤其是人类纠正记录。
      这是三层日志中"最有价值"的层——每一条都是真实反馈。

    路径：{mailbox_dir}/../../logs/l1_human/{msg_id}.json
    （logs/ 与 mailboxes/ 同级，都在 workspace/shared/ 下）
    """
    logs_dir = mailbox_dir.parent / "logs" / "l1_human"
    logs_dir.mkdir(parents=True, exist_ok=True)

    file_path = logs_dir / f"{message['id']}.json"
    lock_path  = file_path.with_suffix(".lock")

    with FileLock(str(lock_path)):
        file_path.write_text(
            json.dumps(message, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def send_mail(
    mailbox_dir: Path,
    to: str,
    from_: str,
    type_: str,
    subject: str,
    content: str,
    project_id: str | None = None,
) -> str:
    """
    发送消息到目标角色的邮箱。

    v6 变更：
      - 新增 project_id（可选，语义 task 标识）
      - type 白名单校验
      - 当 to="human" 时，同时向 L1 日志写入一条记录

    单一接口约束：to=human 时 from_ 必须是 manager。
    """
    if from_ not in _VALID_FROM_ROLES:
        raise ValueError(
            f"未知发件角色 '{from_}'，允许值：{_VALID_FROM_ROLES}"
        )

    if type_ not in _VALID_TYPES:
        raise ValueError(
            f"未知消息类型 '{type_}'，允许值：{sorted(_VALID_TYPES)}"
        )

    if to == "human" and from_ != "manager":
        raise ValueError(
            f"单一接口约束：to=human 时 from_ 必须是 'manager'，"
            f"当前 from_='{from_}'。"
            f"执行层（PM/Dev等）只能发给 manager，由 Manager 决定是否上报给人类。"
        )

    inbox  = _inbox_path(mailbox_dir, to)
    lock   = _lock_path(inbox)
    msg_id = str(uuid.uuid4())

    message = {
        "id":        msg_id,
        "from":      from_,
        "to":        to,
        "type":      type_,
        "subject":   subject,
        "content":   content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read":      False,
    }

    if project_id is not None:
        message["project_id"] = project_id

    with FileLock(str(lock)):
        messages = _read_inbox_file(inbox)
        messages.append(message)
        inbox.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── 第28课新增：L1 日志自动写入 ──────────────────────────────────────────
    if to == "human":
        _write_l1_log(mailbox_dir, message)

    return msg_id


def read_inbox(mailbox_dir: Path, role: str) -> list[dict]:
    """
    读取指定角色的未读消息，并将其标记为已读。
    与第27课完全相同。
    """
    inbox = _inbox_path(mailbox_dir, role)
    lock  = _lock_path(inbox)

    with FileLock(str(lock)):
        messages = _read_inbox_file(inbox)
        unread   = [dict(m) for m in messages if not m.get("read", False)]
        for m in messages:
            if not m.get("read", False):
                m["read"] = True
        inbox.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return unread
