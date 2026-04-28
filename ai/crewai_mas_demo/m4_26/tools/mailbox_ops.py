"""
邮箱操作 Python API — 供单元测试和本地工具直接导入。

三态状态机（类比 AWS SQS Visibility Timeout）：
  send_mail  → status: "unread"
  read_inbox → status: "in_progress" + processing_since（原子操作，防重复取走）
  mark_done  → status: "done"（Agent 处理完后调用）
  reset_stale→ in_progress 超时 → unread（崩溃恢复）

注意：同一逻辑以 CLI 形式在 workspace/*/skills/mailbox/scripts/mailbox_cli.py 中实现，
供 Agent 在沙盒中通过 Bash 调用。两者保持同步。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

# ── 三态常量 ──────────────────────────────────────────────────────────────────
STATUS_UNREAD      = "unread"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE        = "done"

def send_mail(
    mailbox_dir: Path,  # 邮箱目录路径
    to: str,            # 收件人邮箱地址
    from_: str,         # 发件人邮箱地址
    type_: str,         # 邮件类型
    subject: str,
    content: str,       # 邮件内容
) -> str:              # 返回消息ID
    """发送邮件到目标邮箱（filelock 保护）。

    返回消息 ID。消息初始状态为 unread。
    """
    # 收件箱文件路径，基于收件人邮箱地址命名
    inbox_path = mailbox_dir / f"{to}.json"
# 创建一个与输入路径相关联的锁文件路径
# 使用.with_suffix()方法为原始路径添加".json.lock"后缀
    lock_path  = inbox_path.with_suffix(".json.lock")

    msg: dict = {
        "id":               f"msg-{uuid.uuid4().hex[:8]}",
        "from":             from_,
        "to":               to,
        "type":             type_,
        "subject":          subject,
        "content":          content,
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "status":           STATUS_UNREAD,
        "processing_since": None,
    }

    # 使用文件锁确保并发安全
    with FileLock(str(lock_path)):
        # 读取收件箱文件内容，如果文件不存在则初始化为空列表
        # 使用类型注解表明inbox是一个包含字典的列表
        inbox: list[dict] = (
            # 如果收件箱文件存在，则读取其内容并解析为JSON
            json.loads(inbox_path.read_text(encoding="utf-8"))
            # 如果收件箱文件不存在，则使用空列表
            if inbox_path.exists()
            else []
        )
        # 将新消息添加到收件箱列表中
        inbox.append(msg)
        # 将更新后的收件箱列表以JSON格式写回文件
        # ensure_ascii=False 确保非ASCII字符能正确保存
        # indent=2 使JSON文件格式化，提高可读性
        inbox_path.write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return msg["id"]


def read_inbox(mailbox_dir: Path, role: str) -> list[dict]:
    """读取未读消息并原子标记为 in_progress（filelock 保护）。

    返回消息快照（副本），调用方修改快照不影响文件中的数据。
    参数:
        mailbox_dir: 邮箱目录路径
        role: 用户角色标识
    返回:
        list[dict]: 未读消息的快照列表，每个消息是一个字典
    """
    # 构建收件箱文件路径和对应的锁文件路径
    inbox_path = mailbox_dir / f"{role}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")

    # 用于存储未读消息快照的列表
    unread_snapshots: list[dict] = []

    # 使用文件锁确保操作的原子性
    with FileLock(str(lock_path)):
        # 读取收件箱数据，如果文件不存在则初始化为空列表
        inbox: list[dict] = (
            json.loads(inbox_path.read_text(encoding="utf-8"))
            if inbox_path.exists()
            else []
        )
        # 遍历收件箱中的每条消息
        for msg in inbox:
            # 检查消息状态是否为未读
            if msg.get("status") == STATUS_UNREAD:
                # 将消息状态更新为处理中，并记录处理开始时间
                msg["status"]           = STATUS_IN_PROGRESS
                msg["processing_since"] = datetime.now(timezone.utc).isoformat()
                # 添加消息副本到快照列表
                unread_snapshots.append(dict(msg))  # 返回副本
        # 将更新后的收件箱数据写回文件
        inbox_path.write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 返回未读消息的快照列表
    return unread_snapshots


def mark_done(
    mailbox_dir: Path,
    role: str,
    msg_ids: list[str],
) -> int:
    """将指定 in_progress 消息标记为 done。

    返回实际标记数量。
    """
    # 构建收件箱文件路径，基于角色名称
    inbox_path = mailbox_dir / f"{role}.json"
    # 构建锁文件路径，用于文件锁定
    lock_path  = inbox_path.with_suffix(".json.lock")
    # 将消息ID列表转换为集合，便于快速查找
    target_ids = set(msg_ids)
    # 初始化计数器，记录成功标记的消息数量
    count = 0

    # 使用文件锁确保并发安全
    with FileLock(str(lock_path)):
        # 读取收件箱内容，如果文件不存在则初始化为空列表
        inbox: list[dict] = (
            json.loads(inbox_path.read_text(encoding="utf-8"))
            if inbox_path.exists()
            else []
        )
        # 遍历收件箱中的每条消息
        for msg in inbox:
            # 检查消息ID是否在目标集合中，且状态为进行中
            if msg["id"] in target_ids and msg.get("status") == STATUS_IN_PROGRESS:
                # 更新消息状态为已完成
                msg["status"]           = STATUS_DONE
                # 清除处理时间戳
                msg["processing_since"] = None
                # 增加成功计数
                count += 1
        # 将更新后的收件箱内容写回文件
        inbox_path.write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 返回成功标记的消息数量
    return count

def mark_done_all_in_progress(mailbox_dir: Path, role: str) -> int:
    """批量将所有 in_progress 消息标记为 done（Crew 成功后编排器调用）。

    返回标记数量。
    """
    # 定义收件箱文件路径，基于角色名称
    inbox_path = mailbox_dir / f"{role}.json"  # 构建收件箱文件的完整路径
    lock_path  = inbox_path.with_suffix(".json.lock")  # 构建锁文件的完整路径
    count = 0  # 初始化计数器，用于统计标记为done的消息数量

    # 使用文件锁确保并发安全
    with FileLock(str(lock_path)):
        # 读取收件箱数据，如果文件不存在则初始化为空列表
        inbox: list[dict] = (
            json.loads(inbox_path.read_text(encoding="utf-8"))
            if inbox_path.exists()
            else []
        )
        # 遍历收件箱中的每条消息
        for msg in inbox:
            # 检查消息状态是否为"in_progress"
            if msg.get("status") == STATUS_IN_PROGRESS:
                # 将消息状态更新为"done"
                msg["status"]           = STATUS_DONE
                # 清空处理时间戳
                msg["processing_since"] = None
                # 增加计数器
                count += 1
        # 将更新后的收件箱数据写回文件
        inbox_path.write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 返回被标记为done的消息数量
    return count

def reset_stale(
    mailbox_dir: Path,  # 邮箱目录路径
    role: str,         # 角色/用户标识
    timeout_seconds: int = 900,  # 超时时间，默认900秒(15分钟)
) -> int:
    """崩溃恢复：将超时的 in_progress 消息重置为 unread。

    类比 AWS SQS Visibility Timeout 到期后消息重新可见。
    返回重置数量。
    """
    # 构建收件箱文件路径和锁文件路径
    inbox_path = mailbox_dir / f"{role}.json"
    lock_path  = inbox_path.with_suffix(".json.lock")
    count = 0  # 计数器，记录重置的消息数量
    now   = datetime.now(timezone.utc)  # 获取当前UTC时间

    # 使用文件锁确保并发安全
    with FileLock(str(lock_path)):
        # 读取收件箱数据，如果文件不存在则初始化为空列表
        inbox: list[dict] = (
            json.loads(inbox_path.read_text(encoding="utf-8"))
            if inbox_path.exists()
            else []
        )
        # 遍历收件箱中的每条消息
        for msg in inbox:
            # 检查消息是否处于处理中状态且有处理开始时间
            if msg.get("status") == STATUS_IN_PROGRESS and msg.get("processing_since"):
                # 将ISO格式的时间字符串转换为datetime对象
                # 兼容带 +00:00 时区后缀的 ISO 格式（Python 3.11+ 原生支持，低版本需替换）
                started = datetime.fromisoformat(
                    msg["processing_since"].replace("Z", "+00:00")
                )
                # 检查消息处理时间是否超过超时阈值
                if (now - started).total_seconds() > timeout_seconds:
                    # 重置消息状态为未读，并清除处理开始时间
                    msg["status"]           = STATUS_UNREAD
                    msg["processing_since"] = None
                    count += 1  # 增加重置计数
        # 将更新后的收件箱数据写回文件
        inbox_path.write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return count  # 返回重置的消息数量