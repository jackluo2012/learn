"""F6: 结构化日志 handler（全局）——每个事件输出一行 JSON 到 stderr。"""

import json
import sys


def _emit(ctx):
    record = {
        "timestamp": ctx.timestamp,
        "event": ctx.event_type.value,
        "session_id": ctx.session_id,
        "turn": ctx.turn_number,
    }
    if ctx.agent_id:
        record["agent_id"] = ctx.agent_id
    if ctx.tool_name:
        record["tool"] = ctx.tool_name
    if ctx.input_tokens or ctx.output_tokens:
        record["tokens"] = {"input": ctx.input_tokens, "output": ctx.output_tokens}
    print(json.dumps(record, ensure_ascii=False), file=sys.stderr)


def before_turn_handler(ctx):
    _emit(ctx)


def before_llm_handler(ctx):
    _emit(ctx)


def before_tool_handler(ctx):
    _emit(ctx)


def after_tool_handler(ctx):
    _emit(ctx)


def after_turn_handler(ctx):
    _emit(ctx)