"""
第28课·数字员工的自我进化（v8）
schemas.py — 日志记录、复盘报告与改进提案的 Pydantic 数据模型

v8 变更（重构）：
  - 删除 ProposalPatch / ValidationCheck（精确 patch 由 Agent 直接写 before/after_text）
  - 新增 RetroFinding / RetroReport / ImprovementProposal（对齐 SKILL.md 输出格式）
  - 删除 RetroProposal（被 RetroOutput 替代）
  - root_cause 枚举更新：sop_gap / prompt_ambiguity / ability_gap / integration_issue
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator
# ─────────────────────────────────────────────────────────────────────────────
# L2 日志记录（任务-Agent 层）— 保持不变
# ─────────────────────────────────────────────────────────────────────────────

class L2LogRecord(BaseModel):

    """
    L2日志记录模型类，用于记录和验证L2级别的日志数据。
    继承自BaseModel，提供数据验证和序列化功能。
    """
    agent_id:       str  # 代理ID，标识执行任务的代理
    task_id:        str  # 任务ID，标识唯一任务
    task_desc:      str  # 任务描述，说明任务内容
    result_quality: float  # 结果质量评分，范围0.0-1.0
    duration_sec:   float  # 任务执行持续时间（秒）
    error_type:     str | None = None  # 错误类型，可选字段
    timestamp:      str  # 时间戳，采用ISO 8601格式

    @field_validator("result_quality")
    @classmethod
    def quality_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"result_quality 必须在 0.0–1.0 之间，当前值：{v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def valid_iso_timestamp(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError as exc:
            raise ValueError(f"timestamp 格式不合法（需要 ISO 8601），当前值：{v!r}") from exc
        return v
