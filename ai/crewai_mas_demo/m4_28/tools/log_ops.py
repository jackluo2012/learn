"""
第28课·数字员工的自我进化（v6）
tools/log_ops.py — 三层日志读写工具

教学要点（对应第28课 P2）：
  三层日志各有用途：
    L1 人类交互层：由 mailbox_ops.send_mail(to="human") 自动写入
    L2 任务-Agent 层：由 l2_task_callback 在每次 Crew 结束后自动写入
    L3 ReAct 循环层：v6 直接复用 DigitalWorkerCrew 的 session 日志
       → workspace/<agent>/sessions/<session_id>_raw.jsonl
       → workspace/<agent>/sessions/index.jsonl（按 task_id 定位行段）

工程约定（与 mailbox_ops.py 风格一致）：
  - 所有写操作使用 FileLock(path.with_suffix(".lock"))
  - purge_old_l3 基于 record 内的 timestamp 字段判断（不依赖 file mtime）
  - 损坏记录跳过时使用 logging.warning 输出诊断信息
  - 排序使用解析后的 datetime 对象（避免时区格式混用导致的字符串比较错误）
  - 路径规则：
      L1 → logs_dir/l1_human/{msg_id}.json
      L2 → logs_dir/l2_task/{agent_id}_{task_id}.json
      L3（旧）→ logs_dir/l3_react/{agent_id}/{task_id}/step_{N}.json
      L3（v6）→ workspace/<agent>/sessions/ (raw.jsonl + index.jsonl)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from filelock import FileLock

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# L2：任务-Agent 层
# ─────────────────────────────────────────────────────────────────────────────

def write_l2(
    logs_dir: Path,
    agent_id: str,
    task_id: str,
    record: dict,
) -> Path:
    """
    写入一条 L2 日志（任务-Agent 层）。

    文件路径：{logs_dir}/l2_task/{agent_id}_{task_id}.json
    写操作使用 FileLock，与 mailbox_ops 风格一致。

    Args:
        logs_dir:  workspace/shared/logs/ 根目录
        agent_id:  Agent 标识（如 "pm"、"manager"）
        task_id:   任务唯一 ID
        record:    日志内容 dict，应符合 L2LogRecord schema

    Returns:
        写入的文件路径
    """
    # 创建 L2 日志目录
    l2_dir = logs_dir / "l2_task"
    l2_dir.mkdir(parents=True, exist_ok=True)

    # 构建日志文件路径和锁文件路径
    file_path = l2_dir / f"{agent_id}_{task_id}.json"
    lock_path  = file_path.with_suffix(".lock")

    # 使用文件锁确保并发安全地写入日志
    with FileLock(str(lock_path)):
        # 将记录以 JSON 格式写入文件
        file_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 返回写入的文件路径
    return file_path


def read_l2(
    logs_dir: Path,    # 日志目录路径
    agent_id: str,    # Agent 的唯一标识符
    days: int = 7,    # 要读取的天数，默认为7天
) -> list[dict]:    # 返回一个字典列表，每个字典代表一条日志记录
    """
    读取指定 Agent 在 days 天内的 L2 日志，按 timestamp 升序返回。

    只返回 timestamp 在 [now - days, now] 窗口内的记录。
    timestamp 格式为 ISO 8601，解析失败的记录跳过（容错）并写 warning。
    排序基于解析后的 datetime 对象，避免时区格式混用问题。
    """
    l2_dir = logs_dir / "l2_task"    # 构建 L2 日志目录路径
    if not l2_dir.exists():    # 如果目录不存在，返回空列表
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)    # 计算截止时间
    results: list[tuple[datetime, dict]] = []    # 用于存储结果的列表，元素为元组(时间戳, 记录)

    # 遍历匹配 agent_id 的 JSON 文件
    for f in l2_dir.glob(f"{agent_id}_*.json"):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))    # 读取并解析 JSON 文件
            ts = datetime.fromisoformat(record.get("timestamp", ""))    # 解析时间戳
            if ts.tzinfo is None:    # 如果时间戳没有时区信息，设置为 UTC
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:    # 只保留在时间窗口内的记录
                results.append((ts, record))
        except Exception as exc:  # noqa: BLE001    # 捕获并记录异常
            logger.warning("read_l2: 跳过损坏文件 %s: %s", f, exc)
            continue

    results.sort(key=lambda pair: pair[0])    # 按时间戳排序
    return [record for _, record in results]    # 返回排序后的记录列表


# ─────────────────────────────────────────────────────────────────────────────
# L3：ReAct 循环层
# ─────────────────────────────────────────────────────────────────────────────

def write_l3(
    logs_dir: Path,  # 日志目录的路径对象
    agent_id: str,   # 代理的唯一标识符
    task_id: str,    # 任务的唯一标识符
    step_idx: int,   # 步骤索引，用于标识推理-行动步骤的顺序
    record: dict,    # 包含要记录的数据的字典
) -> Path:          # 函数返回写入文件的路径
    """
    写入一条 L3 日志（ReAct 循环层，每个推理-行动步骤一条）。

    文件路径：{logs_dir}/l3_react/{agent_id}/{task_id}/step_{step_idx}.json
    """
    # 构建 L3 日志目录路径
    l3_dir = logs_dir / "l3_react" / agent_id / task_id
    # 创建目录（包括所有必要的父目录），如果目录已存在则不报错
    l3_dir.mkdir(parents=True, exist_ok=True)

    # 构建日志文件路径
    file_path = l3_dir / f"step_{step_idx}.json"
    # 构建锁文件路径，与日志文件相同但扩展名为.lock
    lock_path  = file_path.with_suffix(".lock")

    # 使用文件锁确保并发写入安全
    with FileLock(str(lock_path)):
        # 将记录数据以JSON格式写入文件，ensure_ascii=False支持非ASCII字符，indent=2美化输出
        file_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 返回写入文件的路径
    return file_path


def read_l3(
    logs_dir: Path,  # 日志目录路径
    agent_id: str,   # Agent标识符
    task_id: str,    # 任务标识符
) -> list[dict]:    # 返回包含步骤日志的字典列表
    """读取某 Agent 某任务的全部 L3 步骤日志，按 step_idx 升序。"""
    l3_dir = logs_dir / "l3_react" / agent_id / task_id
    if not l3_dir.exists():
        return []

    steps: list[dict] = []
    for f in sorted(l3_dir.glob("step_*.json")):
        try:
            steps.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            logger.warning("read_l3: 跳过损坏文件 %s: %s", f, exc)
            continue
    return steps


def purge_old_l3(
    logs_dir: Path,  # 日志目录的路径
    retention_days: int = 30,  # 保留天数，默认为30天
) -> int:  # 返回删除的文件数量
    """
    清理 L3 日志中 retention_days 天前的记录。

    判断依据：record 内的 "timestamp" 字段（ISO 8601），而非 file mtime。
    这样测试中无需 os.utime，直接在 record 里写过去的时间即可。

    Returns:
        删除的文件数量
    """
    l3_base = logs_dir / "l3_react"  # L3日志的基础目录路径
    if not l3_base.exists():  # 如果L3日志目录不存在，直接返回0
        return 0

    cutoff  = datetime.now(timezone.utc) - timedelta(days=retention_days)  # 计算截止时间
    deleted = 0  # 删除计数器
 
    # 遍历l3_base目录下所有step_*.json文件
    for f in l3_base.rglob("step_*.json"):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))  # 读取并解析JSON文件
            ts_str = record.get("timestamp", "")  # 获取时间戳字符串
            if not ts_str:  # 如果没有时间戳，跳过
                continue
            ts = datetime.fromisoformat(ts_str)  # 将ISO格式字符串转换为datetime对象
            if ts.tzinfo is None:  # 如果没有时区信息，设置为UTC
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:  # 如果文件时间早于截止时间
                f.unlink(missing_ok=True)
                deleted += 1  # 增加删除计数
        except Exception as exc:  # noqa: BLE001  # 捕获所有异常
            logger.warning("purge_old_l3: 跳过损坏文件 %s: %s", f, exc)  # 记录警告日志
            continue

    return deleted  # 返回删除的文件总数


# ─────────────────────────────────────────────────────────────────────────────
# L3（v6）：从 session 日志读取 ReAct 步骤
# ─────────────────────────────────────────────────────────────────────────────

def read_session_index(sessions_dir: Path) -> list[dict]:
    """
    读取 sessions/index.jsonl，返回全部索引条目。

    每行格式：
      {"session_id","task_id","agent_id","start_ts","end_ts","start_line","end_line"}
    """
    # 构建索引文件的完整路径
    idx_file = sessions_dir / "index.jsonl"
    # 如果索引文件不存在，返回空列表
    if not idx_file.exists():
        return []

    # 用于存储所有索引条目的列表
    entries: list[dict] = []
    # 读取文件内容并按行分割
    for line in idx_file.read_text(encoding="utf-8").splitlines():
        # 去除每行的首尾空白字符
        line = line.strip()
        # 如果行为空，跳过该行
        if not line:
            continue
        try:
            # 将JSON格式的行转换为字典并添加到entries列表中
            entries.append(json.loads(line))
        except Exception as exc:  # noqa: BLE001
            # 如果解析JSON失败，记录警告日志并跳过该行
            logger.warning("read_session_index: 跳过损坏行: %s", exc)
    # 返回所有解析成功的索引条目
    return entries


def read_l3_from_sessions(
    sessions_dir: Path,
    task_id: str | None = None,
    agent_id: str | None = None,
    only_failed: bool = False,
) -> list[dict]:
    """
    v6：从 session 原始日志读取 L3 级别的 ReAct 步骤。

    流程：
      1. 读 index.jsonl 定位 session_id + 行范围
      2. 读 {session_id}_raw.jsonl 的对应行段
      3. 可选按 task_id / agent_id 过滤

    Args:
        sessions_dir: workspace/<agent>/sessions/ 目录
        task_id:      按 task_id 过滤（None 则不过滤）
        agent_id:     按 agent_id 过滤（None 则不过滤）
        only_failed:  只返回含 error/fail 关键词的步骤

    Returns:
        按时间顺序排列的消息列表
    """
    # 从索引文件中读取所有会话条目
    entries = read_session_index(sessions_dir)
    # 如果没有条目，直接返回空列表
    if not entries:
        return []

    # 如果指定了task_id，则过滤出匹配的条目
    if task_id:
        entries = [e for e in entries if e.get("task_id") == task_id]
    # 如果指定了agent_id，则过滤出匹配的条目
    if agent_id:
        entries = [e for e in entries if e.get("agent_id") == agent_id]
    # 如果过滤后没有条目，直接返回空列表
    if not entries:
        return []

    # 用于存储最终结果的列表
    results: list[dict] = []
    # 遍历每个条目
    for entry in entries:
        # 构造原始日志文件路径
        raw_file = sessions_dir / f"{entry['session_id']}_raw.jsonl"
        # 如果文件不存在，记录警告并跳过
        if not raw_file.exists():
            logger.warning("read_l3_from_sessions: 文件不存在 %s", raw_file)
            continue

        # 获取行号范围
        start_line = entry.get("start_line", 0)
        end_line = entry.get("end_line")

        try:
            # 读取文件内容并按行分割
            lines = raw_file.read_text(encoding="utf-8").splitlines()
        except Exception as exc:  # noqa: BLE001
            # 读取失败时记录警告并跳过
            logger.warning("read_l3_from_sessions: 读取失败 %s: %s", raw_file, exc)
            continue

        # 遍历每一行
        for i, line in enumerate(lines):
            # 跳过起始行之前的行
            if i < start_line:
                continue
            # 如果结束行已定义且超出范围，则跳出循环
            if end_line is not None and i >= end_line:
                break
            # 去除行首尾空白
            line = line.strip()
            # 跳过空行
            if not line:
                continue
            try:
                # 解析JSON格式的行内容
                record = json.loads(line)
            except Exception:  # noqa: BLE001
                # 解析失败则跳过该行
                continue

            # 如果只获取失败的步骤，检查内容中是否包含错误关键词
            if only_failed:
                content = str(record.get("content", ""))
                # 如果不包含任何错误关键词，则跳过该记录
                if not any(kw in content.lower() for kw in ("error", "fail", "exception", "traceback")):
                    continue

            results.append(record)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# L1：人类交互层（只读，写入由 mailbox_ops 负责）
# ─────────────────────────────────────────────────────────────────────────────

def read_l1(
    logs_dir: Path,  # 日志目录路径
    days: int = 7,   # 读取天数，默认为7天
) -> list[dict]:    # 返回记录列表，每个记录是一个字典
    """
    读取 L1 日志（人类交互层）中 days 天内的记录，按 timestamp 升序返回。

    L1 日志由 mailbox_ops.send_mail(to="human") 自动写入，
    复盘函数通过此接口读取"人类纠正事件"。
    排序基于解析后的 datetime 对象，避免时区格式混用问题。
    """
    # 构建L1日志目录路径
    l1_dir = logs_dir / "l1_human"
    # 如果目录不存在，返回空列表
    if not l1_dir.exists():
        return []

    # 计算截止时间（当前时间减去指定天数）
    cutoff  = datetime.now(timezone.utc) - timedelta(days=days)
    # 存储结果的列表，元素为元组(时间戳, 记录)
    results: list[tuple[datetime, dict]] = []

    # 遍历目录下所有json文件
    for f in l1_dir.glob("*.json"):
        try:
            # 读取并解析json文件
            record = json.loads(f.read_text(encoding="utf-8"))
            # 获取时间戳并转换为datetime对象
            ts = datetime.fromisoformat(record.get("timestamp", ""))
            # 如果时间戳没有时区信息，设置为UTC时区
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            # 如果时间戳在截止时间之后，添加到结果列表
            if ts >= cutoff:
                results.append((ts, record))
        except Exception as exc:  # noqa: BLE001
            # 记录警告日志并跳过损坏的文件
            logger.warning("read_l1: 跳过损坏文件 %s: %s", f, exc)
            continue

    # 按时间戳排序结果
    results.sort(key=lambda pair: pair[0])
    # 返回排序后的记录列表（不包含时间戳）
    return [record for _, record in results]


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def new_task_id() -> str:
    """生成短 task ID，用于演示。"""
    return str(uuid.uuid4())[:8]


def count_l2_since(logs_dir: Path, agent_id: str, hours: int = 24) -> int:
    """统计 agent_id 在最近 hours 小时内的 L2 日志条数（scheduler 用）。"""
    l2_dir = logs_dir / "l2_task"
    if not l2_dir.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    count = 0
    for f in l2_dir.glob(f"{agent_id}_*.json"):
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(record.get("timestamp", ""))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                count += 1
        except Exception:  # noqa: BLE001
            continue
    return count
