"""F5: CrewAI 机制 → HookRegistry 事件映射。

31课升级：dispatch_gate + pending_deny + success 检测 + token 估算。
30课对齐：prompt_preview / tool_input / tool_output / llm_response 富元数据。

注意：不使用 @after_llm_call —— 注册该 hook 会干扰 CrewAI
的 function calling 工具调度。LLM 回复数据改从 step_callback 获取。

映射关系：
┌──────────────────────────┬───────────────────────────┐
│ @before_llm_call         │ BEFORE_TURN（首次）       │
│                          │ BEFORE_LLM（每次）        │
│ @before_tool_call        │ BEFORE_TOOL_CALL (gate)   │
│ @after_tool_call         │ AFTER_TOOL_CALL (gate)    │
│ step_callback            │ AFTER_TURN (gate)         │
│ task_callback            │ TASK_COMPLETE             │
└──────────────────────────┴───────────────────────────┘
"""

from typing import Callable

from crewai.hooks import (
    after_tool_call,
    before_llm_call,
    before_tool_call,
    clear_after_tool_call_hooks,
    clear_before_llm_call_hooks,
    clear_before_tool_call_hooks,
)

from .registry import EventType, GuardrailDeny, HookContext, HookRegistry

_MAX_TEXT = 2000


def _truncate(text: str, limit: int = _MAX_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated, {len(text)} chars total]"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) * 2 // 3)


class CrewObservabilityAdapter:
    def __init__(self, registry: HookRegistry, session_id: str = ""):
        self._registry = registry
        self._session_id = session_id
        self._turn_count = 0
        self._current_turn_has_llm = False
        self._cleaned = False
        self._pending_input_tokens = 0
        self._pending_deny: GuardrailDeny | None = None
        self._last_agent_role = ""
        self._task_description = ""
        self._last_prompt_preview = ""

    def install_global_hooks(self):

        """
        安装全局钩子函数，用于在LLM调用和工具调用前后执行特定操作。
        这些钩子函数用于监控和记录会话、代理和工具的交互情况。
        """
        registry = self._registry  # 获取注册表对象
        sid = self._session_id  # 获取会话ID

        # 在LLM调用前执行的钩子函数
        @before_llm_call
        def _before_llm(context):
            """
            在LLM调用前执行的函数，用于记录代理角色、任务描述，
            以及更新计数器和派发相应的事件。
            """
            # 获取代理ID
            agent_id = getattr(getattr(context, "agent", None), "role", "")
            self._last_agent_role = agent_id  # 记录最后使用的代理角色

            # 获取任务描述
            task = getattr(context, "task", None)
            if task and not self._task_description:
                self._task_description = _truncate(
                    getattr(task, "description", "") or ""
                )

            # 如果当前回合没有LLM调用，则增加回合计数并派发BEFORE_TURN事件
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

            # 从 LLM 对象提取真实模型名（Sub-Crew 使用不同模型时正确记录）
            llm_model = ""
            llm = getattr(context, "llm", None)
            if llm:
                llm_model = getattr(llm, "model", "") or ""
                if isinstance(llm_model, str) and "/" in llm_model:
                    llm_model = llm_model.rsplit("/", 1)[-1]

            messages = getattr(context, "messages", [])
            preview = ""
            if messages:
                last_msg = messages[-1]
                content = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
                preview = _truncate(str(content), 500)
                self._pending_input_tokens = _estimate_tokens(
                    "".join(str(m) for m in messages)
                )
            else:
                self._pending_input_tokens = 0
            self._last_prompt_preview = preview

            registry.dispatch(
                EventType.BEFORE_LLM,
                HookContext(
                    event_type=EventType.BEFORE_LLM,
                    agent_id=agent_id,
                    session_id=sid,
                    turn_number=self._turn_count,
                    input_tokens=self._pending_input_tokens,
                    metadata={"prompt_preview": preview, "model": llm_model},
                ),
            )
            return None

        @before_tool_call
        def _before_tool(context):
            """
            在工具调用前执行的钩子函数，用于检查是否拒绝调用并派发BEFORE_TOOL_CALL事件。
            """
            if self._pending_deny:
                return False
            try:
                registry.dispatch_gate(
                    EventType.BEFORE_TOOL_CALL,
                    HookContext(
                        event_type=EventType.BEFORE_TOOL_CALL,
                        tool_name=context.tool_name,
                        tool_input=dict(context.tool_input or {}),
                        session_id=sid,
                        turn_number=self._turn_count,
                    ),
                )
            except GuardrailDeny as e:
                self._pending_deny = e
                return False
            return None

        @after_tool_call
        def _after_tool(context):
            """
            在工具调用后执行的钩子函数，用于处理工具调用的结果，
            检查是否出现错误，并派发AFTER_TOOL_CALL事件。
            """
            tool_result = _truncate(
                str(getattr(context, "tool_result", "") or "")
            )
            is_error = any(
                kw in tool_result.lower()
                for kw in ["error", "exception", "traceback", "failed"]
            )
            try:
                registry.dispatch_gate(
                    EventType.AFTER_TOOL_CALL,
                    HookContext(
                        event_type=EventType.AFTER_TOOL_CALL,
                        tool_name=context.tool_name,
                        tool_input=dict(context.tool_input or {}),
                        success=not is_error,
                        session_id=sid,
                        turn_number=self._turn_count,
                        metadata={"tool_output": tool_result},
                    ),
                )
            except GuardrailDeny as e:
                self._pending_deny = e

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

            est_output_tokens = _estimate_tokens(step_output)

            try:
                registry.dispatch_gate(
                    EventType.AFTER_TURN,
                    HookContext(
                        event_type=EventType.AFTER_TURN,
                        session_id=sid,
                        turn_number=self._turn_count,
                        agent_id=self._last_agent_role,
                        tool_name=tool_name,
                        input_tokens=self._pending_input_tokens,
                        output_tokens=est_output_tokens,
                        metadata={
                            "output": step_output,
                            "llm_response": llm_response,
                            "prompt_preview": self._last_prompt_preview,
                        },
                    ),
                )
            finally:
                self._current_turn_has_llm = False
                self._pending_input_tokens = 0
                self._last_prompt_preview = ""

            pending = self._pending_deny
            self._pending_deny = None
            if pending:
                raise pending

        return callback

    def make_sub_crew_step_callback(self) -> Callable:
        """Sub-Crew 专用 step_callback。

        设计要点：
        - 独立 sub_turn 计数，不污染主 Crew 的 _turn_count
        - 不重置 _current_turn_has_llm（主 Crew 仍需要它）
        - 从全局 @before_llm_call 已写入的 _last_agent_role / _pending_input_tokens 读值
        - 用 registry.dispatch（非 gate），避免 Sub-Crew 触发主 Crew 的 pending_deny 机制
        """
        registry = self._registry
        sid = self._session_id
        sub_turn = [0]

        def callback(step):
            from crewai.agents.parser import AgentAction, AgentFinish

            sub_turn[0] += 1
            step_output = tool_name = llm_response = ""

            if isinstance(step, AgentAction):
                tool_name    = getattr(step, "tool",   "")
                step_output  = _truncate(str(getattr(step, "result", "") or ""))
                llm_response = _truncate(str(getattr(step, "text",   "") or ""))
            elif isinstance(step, AgentFinish):
                step_output  = _truncate(str(getattr(step, "output", "")))
                llm_response = _truncate(str(getattr(step, "text",   "") or ""))

            registry.dispatch(
                EventType.AFTER_TURN,
                HookContext(
                    event_type=EventType.AFTER_TURN,
                    session_id=sid,
                    turn_number=sub_turn[0],
                    agent_id=self._last_agent_role,
                    tool_name=tool_name,
                    input_tokens=self._pending_input_tokens,
                    output_tokens=_estimate_tokens(step_output),
                    metadata={
                        "output": step_output,
                        "llm_response": llm_response,
                        "prompt_preview": self._last_prompt_preview,
                        "sub_crew": True,
                    },
                ),
            )
            # 只清 token 状态，不动 _current_turn_has_llm（主 Crew 仍需要它）
            self._pending_input_tokens = 0
            self._last_prompt_preview  = ""

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