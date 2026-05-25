"""F5: CrewAI 机制 → HookRegistry 事件映射。

映射关系：
┌──────────────────────────┬───────────────────────────┐
│ @before_llm_call         │ BEFORE_TURN（首次）       │
│                          │ BEFORE_LLM（每次）        │
│ @before_tool_call        │ BEFORE_TOOL_CALL          │
│ @after_tool_call         │ AFTER_TOOL_CALL           │
│ step_callback            │ AFTER_TURN                │
│ task_callback            │ TASK_COMPLETE             │
└──────────────────────────┴───────────────────────────┘

注意：不使用 @after_llm_call —— 注册该 hook 会干扰 CrewAI
的 function calling 工具调度，导致 LLM 返回的 tool_call 被当作
final answer 而非触发工具执行。LLM 回复数据改从 step_callback
中的 AgentFinish.output / AgentAction.result 获取。
"""

from typing import Callable

# 导入 CrewAI 的钩子相关模块
from crewai.hooks import (
    after_tool_call,
    before_llm_call,
    before_tool_call,
    clear_after_tool_call_hooks,
    clear_before_llm_call_hooks,
    clear_before_tool_call_hooks,
)

# 从本地模块导入事件类型、钩子上下文和钩子注册表
from .registry import EventType, HookContext, HookRegistry

# 定义文本截断的最大长度常量
_MAX_TEXT = 2000

def _truncate(text: str, limit: int = _MAX_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated, {len(text)} chars total]"
class CrewObservabilityAdapter:
    def __init__(self, registry: HookRegistry, session_id: str = ""):
        self._registry = registry
        self._session_id = session_id
        self._turn_count = 0
        self._current_turn_has_llm = False
        self._cleaned = False
        self._last_agent_role = ""
        self._task_description = ""
        self._last_prompt_preview = ""

    def install_global_hooks(self):
        registry = self._registry
        sid = self._session_id

        @before_llm_call
        def _before_llm(context):
            agent_id = getattr(getattr(context, "agent", None), "role", "")
            self._last_agent_role = agent_id

            task = getattr(context, "task", None)
            if task and not self._task_description:
                self._task_description = _truncate(
                    getattr(task, "description", "") or ""
                )

            if not self._current_turn_has_llm:
                self._turn_count += 1
                self._current_turn_has_llm = True
                registry.dispatch(
                    EventType.BEFORE_TURN,
                    HookContext(
                        event_type=EventType.BEFORE_TURN,
                        agent_id=agent_id,
                        session_id=sid,
                        turn_number=self._turn_count,
                    ),
                )

            messages = getattr(context, "messages", [])
            preview = ""
            if messages:
                last_msg = messages[-1]
                content = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
                preview = _truncate(str(content), 500)

            # 从 LLM 对象提取真实模型名（Sub-Crew 使用不同模型时正确记录）
            llm_model = ""
            llm = getattr(context, "llm", None)
            if llm:
                llm_model = getattr(llm, "model", "") or ""
                if isinstance(llm_model, str) and "/" in llm_model:
                    llm_model = llm_model.rsplit("/", 1)[-1]

            self._last_prompt_preview = preview

            registry.dispatch(
                EventType.BEFORE_LLM,
                HookContext(
                    event_type=EventType.BEFORE_LLM,
                    agent_id=agent_id,
                    session_id=sid,
                    turn_number=self._turn_count,
                    metadata={"prompt_preview": preview, "model": llm_model},
                ),
            )
            return None

        @before_tool_call
        def _before_tool(context):
            registry.dispatch(
                EventType.BEFORE_TOOL_CALL,
                HookContext(
                    event_type=EventType.BEFORE_TOOL_CALL,
                    tool_name=context.tool_name,
                    tool_input=dict(context.tool_input or {}),
                    session_id=sid,
                    turn_number=self._turn_count,
                ),
            )
            return None

        @after_tool_call
        def _after_tool(context):
            tool_result = _truncate(
                str(getattr(context, "tool_result", "") or "")
            )
            registry.dispatch(
                EventType.AFTER_TOOL_CALL,
                HookContext(
                    event_type=EventType.AFTER_TOOL_CALL,
                    tool_name=context.tool_name,
                    tool_input=dict(context.tool_input or {}),
                    session_id=sid,
                    turn_number=self._turn_count,
                    metadata={"tool_output": tool_result},
                ),
            )

    def make_step_callback(self) -> Callable:
        registry = self._registry
        sid = self._session_id

        def callback(step):
            from crewai.agents.parser import AgentAction, AgentFinish

            step_output = ""
            tool_name = ""
            llm_response = ""

            if isinstance(step, AgentAction):
                tool_name = getattr(step, "tool", "")
                step_output = _truncate(str(getattr(step, "result", "") or ""))
                llm_response = _truncate(str(getattr(step, "text", "") or ""))
            elif isinstance(step, AgentFinish):
                step_output = _truncate(str(getattr(step, "output", "")))
                llm_response = _truncate(str(getattr(step, "text", "") or ""))

            registry.dispatch(
                EventType.AFTER_TURN,
                HookContext(
                    event_type=EventType.AFTER_TURN,
                    session_id=sid,
                    turn_number=self._turn_count,
                    agent_id=self._last_agent_role,
                    tool_name=tool_name,
                    metadata={
                        "output": step_output,
                        "llm_response": llm_response,
                        "prompt_preview": self._last_prompt_preview,
                    },
                ),
            )
            self._current_turn_has_llm = False
            self._last_prompt_preview = ""

        return callback

    def make_task_callback(self) -> Callable:
        registry = self._registry
        sid = self._session_id

        def callback(task_output):
            raw = _truncate(str(getattr(task_output, "raw", str(task_output))))
            desc = getattr(task_output, "description", "") or self._task_description

            registry.dispatch(
                EventType.TASK_COMPLETE,
                HookContext(
                    event_type=EventType.TASK_COMPLETE,
                    session_id=sid,
                    task_name=_truncate(str(desc), 500),
                    agent_id=self._last_agent_role,
                    metadata={
                        "raw_output": raw,
                        "task_description": _truncate(str(desc), 500),
                    },
                ),
            )

        return callback

    def cleanup(self):
        if self._cleaned:
            return
        self._cleaned = True
        self._registry.dispatch(
            EventType.SESSION_END,
            HookContext(
                event_type=EventType.SESSION_END,
                session_id=self._session_id,
            ),
        )
        clear_before_llm_call_hooks()
        clear_before_tool_call_hooks()
        clear_after_tool_call_hooks()