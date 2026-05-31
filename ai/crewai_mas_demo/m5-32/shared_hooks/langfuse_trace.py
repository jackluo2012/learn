"""F7: Langfuse 追踪 handler（全局）——Langfuse v4 SDK 批量注入 API。

架构要点：
- ContextVar 实现线程/异步安全（Sub-Crew 通过 copy_context() + ctx.run() 继承上下文）
- 批量注入 API（ingestion.batch()）替代 OTel SDK，彻底消除 OTel 线程依赖
- GENERATION 在每次 LLM call（BEFORE_LLM）开启，AFTER_TURN 关闭
- TOOL span 在 BEFORE_TOOL_CALL 开启，AFTER_TOOL_CALL 关闭
- Sub-Crew 通过 _reset_subcrew_state(parent_span_id) 挂在 skill_loader span 下
"""

import atexit
import hashlib
import logging
import os
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from threading import Lock

logger = logging.getLogger(__name__)

# ── 客户端（模块级单例，跨线程共享只读） ─────────────────────────────────────
_client = None
_init_failed = False
_batch_buffer: list = []
_batch_lock = Lock()

# ── 每线程/协程独立状态（ContextVar）────────────────────────────────────────
_trace_id_var: ContextVar[str] = ContextVar("lf_trace_id", default="")
_session_id_var: ContextVar[str] = ContextVar("lf_session_id", default="")
_root_span_id_var: ContextVar[str] = ContextVar("lf_root_span_id", default="")
_gen_id_var: ContextVar[str] = ContextVar("lf_gen_id", default="")
_gen_count_var: ContextVar[int] = ContextVar("lf_gen_count", default=0)
_tool_count_var: ContextVar[int] = ContextVar("lf_tool_count", default=0)
_span_stack_var: ContextVar[tuple] = ContextVar("lf_span_stack", default=())


# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _ensure_client():
    global _client, _init_failed
    if _init_failed:
        return None
    if _client is None:
        try:
            from langfuse import Langfuse
            pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
            sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
            if not (pk and sk):
                _init_failed = True
                logger.debug("langfuse disabled: LANGFUSE_PUBLIC_KEY / SECRET_KEY not set")
                return None
            # host / base_url 由 SDK 从 LANGFUSE_BASE_URL / LANGFUSE_HOST env 自动读取
            _client = Langfuse(tracing_enabled=False, public_key=pk, secret_key=sk)
            atexit.register(_flush_batch)
        except Exception:
            _init_failed = True
            logger.debug("langfuse init failed (non-blocking)", exc_info=True)
            return None
    return _client


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


def _enqueue(event) -> None:
    with _batch_lock:
        _batch_buffer.append(event)


def _flush_batch() -> None:
    global _batch_buffer
    with _batch_lock:
        if not _batch_buffer:
            return
        batch = _batch_buffer[:]
        _batch_buffer = []
    client = _ensure_client()
    if client is None:
        return
    chunk_size = 50
    for i in range(0, len(batch), chunk_size):
        try:
            client.api.ingestion.batch(batch=batch[i: i + chunk_size])
        except Exception:
            logger.debug("langfuse batch flush failed (non-blocking)", exc_info=True)


def _get_gen_parent_id() -> str:
    """Generation 的父节点：栈顶 span > root span。"""
    stack = _span_stack_var.get(())
    if stack:
        return stack[-1][0]
    return _root_span_id_var.get("")


def _get_tool_parent_id() -> str:
    """Tool span 的父节点：当前 gen > 栈顶 span > root span。"""
    gen_id = _gen_id_var.get("")
    if gen_id:
        return gen_id
    stack = _span_stack_var.get(())
    if stack:
        return stack[-1][0]
    return _root_span_id_var.get("")


# ── Sub-Crew 辅助函数（供 skill_loader_tool._run() 调用） ────────────────────

def _get_langfuse_parent_span_id() -> str:
    """主线程在 spawn 子线程前读取当前父 span ID（传给 _reset_subcrew_state）。"""
    stack = _span_stack_var.get(())
    if stack:
        return stack[-1][0]
    return _root_span_id_var.get("")


def _reset_subcrew_state(parent_span_id: str = "") -> None:
    """在 Sub-Crew 新线程中重置 per-gen 计数器，将 root 设为 skill_loader span。

    保留 _trace_id_var（Sub-Crew span 需要挂到同一 trace）。
    清空 span 栈（Sub-Crew 不继承主线程的栈）。
    """
    if parent_span_id:
        _root_span_id_var.set(parent_span_id)
    _gen_id_var.set("")
    _gen_count_var.set(0)
    _tool_count_var.set(0)
    _span_stack_var.set(())


def subcrew_cleanup() -> None:
    """关闭 Sub-Crew 遗留的 gen/span，然后 flush batch。"""
    gen_id = _gen_id_var.get("")
    if gen_id:
        from langfuse.api import UpdateGenerationBody
        from langfuse.api.ingestion.types import IngestionEvent_GenerationUpdate

        _enqueue(
            IngestionEvent_GenerationUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="generation-update",
                body=UpdateGenerationBody(id=gen_id, end_time=_now()),
            )
        )
        _gen_id_var.set("")

    stack = _span_stack_var.get(())
    if stack:
        from langfuse.api import UpdateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanUpdate

        for entry in stack:
            _enqueue(
                IngestionEvent_SpanUpdate(
                    id=_uid(),
                    timestamp=_now().isoformat(),
                    type="span-update",
                    body=UpdateSpanBody(
                        id=entry[0],
                        end_time=_now(),
                        metadata={"phase": "subcrew-cleanup"},
                    ),
                )
            )
        _span_stack_var.set(())

    _flush_batch()


# ── Trace 初始化 ──────────────────────────────────────────────────────────────

def _ensure_trace(ctx) -> str | None:
    """确保当前 ContextVar 中有 trace_id + root span，幂等。"""
    if _trace_id_var.get(""):
        return _trace_id_var.get()

    client = _ensure_client()
    if client is None:
        return None

    # 与 Langfuse.create_trace_id(seed=session_id) 行为一致（sha256 前16字节 hex）
    # 确保 T16 集成测试通过 client.create_trace_id(seed=session_id) 能查到同一 trace
    seed = ctx.session_id or ""
    trace_id = (
        hashlib.sha256(seed.encode("utf-8")).digest()[:16].hex()
        if seed
        else _uid()
    )
    _trace_id_var.set(trace_id)
    _session_id_var.set(ctx.session_id)

    from langfuse.api import CreateSpanBody, TraceBody
    from langfuse.api.ingestion.types import (
        IngestionEvent_SpanCreate,
        IngestionEvent_TraceCreate,
    )

    _enqueue(
        IngestionEvent_TraceCreate(
            id=_uid(),
            timestamp=_now().isoformat(),
            type="trace-create",
            body=TraceBody(
                id=trace_id,
                name=f"agent-run-{ctx.session_id}",
                session_id=ctx.session_id,
                metadata={"source": "m5l31-hook-framework"},
            ),
        )
    )

    root_id = _uid()
    _root_span_id_var.set(root_id)

    _enqueue(
        IngestionEvent_SpanCreate(
            id=_uid(),
            timestamp=_now().isoformat(),
            type="span-create",
            body=CreateSpanBody(
                id=root_id,
                trace_id=trace_id,
                name=f"session-{ctx.session_id}",
                start_time=_now(),
                metadata={"session_id": ctx.session_id, "source": "m5l31-hook-framework"},
            ),
        )
    )

    return trace_id


# ── Event Handlers ────────────────────────────────────────────────────────────

def before_llm_handler(ctx) -> None:
    """BEFORE_LLM: 关闭前一个 generation（若存在），开启新的 generation。"""
    _ensure_trace(ctx)

    prev_gen_id = _gen_id_var.get("")
    if prev_gen_id:
        from langfuse.api import UpdateGenerationBody
        from langfuse.api.ingestion.types import IngestionEvent_GenerationUpdate

        _enqueue(
            IngestionEvent_GenerationUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="generation-update",
                body=UpdateGenerationBody(id=prev_gen_id, end_time=_now()),
            )
        )

    count = _gen_count_var.get(0) + 1
    _gen_count_var.set(count)
    gen_id = _uid()
    _gen_id_var.set(gen_id)

    prompt_preview = ctx.metadata.get("prompt_preview", "")
    model = ctx.metadata.get("model", "") or os.environ.get("AGENT_MODEL", "qwen-plus")

    from langfuse.api import CreateGenerationBody
    from langfuse.api.ingestion.types import IngestionEvent_GenerationCreate

    _enqueue(
        IngestionEvent_GenerationCreate(
            id=_uid(),
            timestamp=_now().isoformat(),
            type="generation-create",
            body=CreateGenerationBody(
                id=gen_id,
                trace_id=_trace_id_var.get(""),
                parent_observation_id=_get_gen_parent_id() or None,
                name=f"llm-call-{count}",
                model=model,
                start_time=_now(),
                input={"prompt": prompt_preview} if prompt_preview else None,
                metadata={
                    "agent_id": ctx.agent_id,
                    "turn": ctx.turn_number,
                    "call_number": count,
                },
            ),
        )
    )


def before_tool_handler(ctx) -> None:
    """BEFORE_TOOL_CALL: 开启 TOOL span，入栈。"""
    _ensure_trace(ctx)

    tool_input = dict(ctx.tool_input) if ctx.tool_input else {}
    _tool_count_var.set(_tool_count_var.get(0) + 1)

    span_id = _uid()
    trace_id = _trace_id_var.get("")

    from langfuse.api import CreateSpanBody
    from langfuse.api.ingestion.types import IngestionEvent_SpanCreate

    _enqueue(
        IngestionEvent_SpanCreate(
            id=_uid(),
            timestamp=_now().isoformat(),
            type="span-create",
            body=CreateSpanBody(
                id=span_id,
                trace_id=trace_id,
                parent_observation_id=_get_tool_parent_id() or None,
                name=f"tool-{ctx.tool_name}",
                start_time=_now(),
                input=tool_input or None,
                metadata={"tool": ctx.tool_name, "turn": ctx.turn_number},
            ),
        )
    )

    old_stack = _span_stack_var.get(())
    _span_stack_var.set((*old_stack, (span_id, ctx.tool_name, ctx.turn_number, tool_input)))


def after_tool_handler(ctx) -> None:
    """AFTER_TOOL_CALL: 关闭 TOOL span，出栈。"""
    tool_output = ctx.metadata.get("tool_output", "")
    is_deny = ctx.metadata.get("guardrail_deny", False)
    level = "ERROR" if (not ctx.success or is_deny) else "DEFAULT"

    output_body: dict = {"success": ctx.success}
    if tool_output:
        output_body["result"] = tool_output
    if is_deny:
        output_body["deny_reason"] = ctx.metadata.get("deny_reason", "")

    # 从栈中逆序找到匹配的 span
    stack = list(_span_stack_var.get(()))
    matched_id = None
    key = (ctx.tool_name, ctx.turn_number)
    for i in range(len(stack) - 1, -1, -1):
        if (stack[i][1], stack[i][2]) == key:
            matched_id = stack.pop(i)[0]
            break
    _span_stack_var.set(tuple(stack))

    if matched_id:
        from langfuse.api import UpdateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanUpdate

        _enqueue(
            IngestionEvent_SpanUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="span-update",
                body=UpdateSpanBody(
                    id=matched_id,
                    output=output_body,
                    level=level,
                    end_time=_now(),
                    metadata={"tool": ctx.tool_name, "duration_ms": ctx.duration_ms},
                ),
            )
        )
    else:
        # 找不到匹配 span 时，直接建完整 span
        _ensure_trace(ctx)
        span_id = _uid()

        from langfuse.api import CreateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanCreate

        _enqueue(
            IngestionEvent_SpanCreate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="span-create",
                body=CreateSpanBody(
                    id=span_id,
                    trace_id=_trace_id_var.get(""),
                    parent_observation_id=_get_tool_parent_id() or None,
                    name=f"tool-{ctx.tool_name}",
                    start_time=_now(),
                    end_time=_now(),
                    input=dict(ctx.tool_input) if ctx.tool_input else None,
                    output=output_body,
                    level=level,
                    metadata={"tool": ctx.tool_name, "duration_ms": ctx.duration_ms},
                ),
            )
        )


def after_turn_handler(ctx) -> None:
    """AFTER_TURN: 关闭当前 generation，写入 output + token 数据。"""
    _ensure_trace(ctx)

    step_output = ctx.metadata.get("output", "")
    llm_response = ctx.metadata.get("llm_response", "")
    gen_output = llm_response or step_output or None

    gen_id = _gen_id_var.get("")
    if gen_id:
        from langfuse.api import UpdateGenerationBody
        from langfuse.api.ingestion.types import IngestionEvent_GenerationUpdate

        update_kwargs: dict = {"id": gen_id, "end_time": _now()}
        if gen_output:
            update_kwargs["output"] = gen_output
        if ctx.input_tokens or ctx.output_tokens:
            from langfuse.api.commons.types.usage import Usage

            update_kwargs["usage"] = Usage(
                input=ctx.input_tokens,
                output=ctx.output_tokens,
                total=(ctx.input_tokens or 0) + (ctx.output_tokens or 0),
            )

        _enqueue(
            IngestionEvent_GenerationUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="generation-update",
                body=UpdateGenerationBody(**update_kwargs),
            )
        )
        _gen_id_var.set("")

    # 自动关闭遗留的 tool span
    stack = _span_stack_var.get(())
    if stack:
        from langfuse.api import UpdateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanUpdate

        for entry in stack:
            _enqueue(
                IngestionEvent_SpanUpdate(
                    id=_uid(),
                    timestamp=_now().isoformat(),
                    type="span-update",
                    body=UpdateSpanBody(
                        id=entry[0],
                        end_time=_now(),
                        metadata={"phase": "auto-closed-by-after-turn"},
                    ),
                )
            )
        _span_stack_var.set(())


def task_complete_handler(ctx) -> None:
    """TASK_COMPLETE: 记录任务完成，更新 trace + root span 的 input/output。"""
    _ensure_trace(ctx)

    task_desc = ctx.metadata.get("task_description", ctx.task_name)
    raw_output = ctx.metadata.get("raw_output", "")
    trace_id = _trace_id_var.get("")
    root_id = _root_span_id_var.get("")

    from langfuse.api import CreateSpanBody, TraceBody, UpdateSpanBody
    from langfuse.api.ingestion.types import (
        IngestionEvent_SpanCreate,
        IngestionEvent_SpanUpdate,
        IngestionEvent_TraceCreate,
    )

    # task-complete span（任务完成详情）
    _enqueue(
        IngestionEvent_SpanCreate(
            id=_uid(),
            timestamp=_now().isoformat(),
            type="span-create",
            body=CreateSpanBody(
                id=_uid(),
                trace_id=trace_id,
                parent_observation_id=root_id or None,
                name="task-complete",
                start_time=_now(),
                end_time=_now(),
                input=task_desc or None,
                output=raw_output or None,
                metadata={"agent": ctx.agent_id},
            ),
        )
    )

    # 更新 trace 级别的 input/output（Langfuse 左侧面板显示的最外层）
    if trace_id and (task_desc or raw_output):
        _enqueue(
            IngestionEvent_TraceCreate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="trace-create",
                body=TraceBody(
                    id=trace_id,
                    input=task_desc or None,
                    output=raw_output or None,
                ),
            )
        )

    # 更新 root span 的 input/output（session 级别的 span）
    if root_id and (task_desc or raw_output):
        _enqueue(
            IngestionEvent_SpanUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="span-update",
                body=UpdateSpanBody(
                    id=root_id,
                    input=task_desc or None,
                    output=raw_output or None,
                ),
            )
        )


def flush_and_close(ctx) -> None:
    """SESSION_END: 清理孤儿 span/gen，关闭 root span，flush batch。"""
    # 关闭遗留 gen
    gen_id = _gen_id_var.get("")
    if gen_id:
        from langfuse.api import UpdateGenerationBody
        from langfuse.api.ingestion.types import IngestionEvent_GenerationUpdate

        _enqueue(
            IngestionEvent_GenerationUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="generation-update",
                body=UpdateGenerationBody(
                    id=gen_id,
                    level="WARNING",
                    status_message="orphaned-gen-auto-closed",
                    end_time=_now(),
                ),
            )
        )
        _gen_id_var.set("")

    # 关闭遗留 tool span
    stack = _span_stack_var.get(())
    if stack:
        from langfuse.api import UpdateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanUpdate

        for entry in stack:
            _enqueue(
                IngestionEvent_SpanUpdate(
                    id=_uid(),
                    timestamp=_now().isoformat(),
                    type="span-update",
                    body=UpdateSpanBody(
                        id=entry[0],
                        level="WARNING",
                        status_message="orphaned-span-auto-closed",
                        end_time=_now(),
                    ),
                )
            )
        _span_stack_var.set(())

    # 关闭 root span
    root_id = _root_span_id_var.get("")
    if root_id:
        from langfuse.api import UpdateSpanBody
        from langfuse.api.ingestion.types import IngestionEvent_SpanUpdate

        _enqueue(
            IngestionEvent_SpanUpdate(
                id=_uid(),
                timestamp=_now().isoformat(),
                type="span-update",
                body=UpdateSpanBody(id=root_id, end_time=_now()),
            )
        )

    _flush_batch()

    # 重置所有 ContextVar
    _trace_id_var.set("")
    _session_id_var.set("")
    _root_span_id_var.set("")
    _gen_id_var.set("")
    _gen_count_var.set(0)
    _tool_count_var.set(0)
    _span_stack_var.set(())