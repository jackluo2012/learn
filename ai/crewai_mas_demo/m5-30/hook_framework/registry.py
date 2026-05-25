"""F1-F2: EventType 枚举 + HookContext 数据类 + HookRegistry 核心分发。"""

import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable



class EventType(Enum):
    BEFORE_TURN = "before_turn"
    BEFORE_LLM = "before_llm"
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    AFTER_TURN = "after_turn"
    TASK_COMPLETE = "task_complete"
    SESSION_END = "session_end"


@dataclass(frozen=True)
class HookContext:

    """
    HookContext类用于存储和管理钩子上下文信息，记录事件相关的各种数据。
    包含事件类型、时间戳、代理ID、任务名称等多种字段。
    """
    event_type: EventType  # 事件类型，使用EventType枚举类型
    timestamp: str = field(  # 时间戳字段，默认值为当前UTC时间的ISO格式
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    agent_id: str = ""  # 代理ID，默认为空字符串
    task_name: str = ""  # 任务名称，默认为空字符串
    tool_name: str = ""  # 工具名称，默认为空字符串
    tool_input: dict = field(default_factory=dict)  # 工具输入参数，默认为空字典
    input_tokens: int = 0  # 输入令牌数，默认为0
    output_tokens: int = 0  # 输出令牌数，默认为0
    duration_ms: float = 0  # 持续时间（毫秒），默认为0
    success: bool = True  # 执行是否成功，默认为True
    session_id: str = ""  # 会话ID，默认为空字符串
    turn_number: int = 0  # 轮次编号，默认为0
    metadata: dict = field(default_factory=dict)  # 元数据，默认为空字典


class HookRegistry:
    def __init__(self):
        # 初始化两个字典，分别用于存储事件处理函数和处理函数名称
        # _handlers: 键为事件类型，值为处理函数列表
        # _handler_names: 键为事件类型，值为处理函数名称列表
        self._handlers: dict[EventType, list[Callable]] = defaultdict(list)
        self._handler_names: dict[EventType, list[str]] = defaultdict(list)

    def register(self, event_type: EventType, handler: Callable, name: str = ""):
        self._handlers[event_type].append(handler)
        self._handler_names[event_type].append(name or getattr(handler, "__name__", repr(handler)))

    def dispatch(self, event_type: EventType, context: HookContext):
        for handler in self._handlers[event_type]:
            try:
                handler(context)
            except Exception as e:
                print(
                    f"[HookRegistry] {event_type.value} handler error: {e}\n"
                    f"{traceback.format_exc()}",
                    file=sys.stderr,
                )

    def handler_count(self, event_type: EventType) -> int:
        return len(self._handlers[event_type])

    def summary(self) -> dict[str, list[str]]:
        return {
            et.value: list(names)
            for et, names in self._handler_names.items()
            if names
        }