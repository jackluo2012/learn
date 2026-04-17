"""
indexer.py — 对话记忆写入 pipeline

职责：
  1. 解析 session JSONL，按轮次切 chunk（user + assistant 一问一答）
  2. 调 qwen3-turbo 提取摘要 + 标签
  3. 调 text-embedding-v3 向量化（摘要 + 原始对话）
  4. 写入 pgvector

💡 核心点：设计为异步函数，可在每轮对话结束后后台触发，不阻塞主流程
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from openai import OpenAI
# ─────────────────────────────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────────────────────────────
DB_DSN = os.getenv(
    "MEMORY_DB_DSN",
    "postgresql://jackclaw:jackclaw123@localhost:5432/jackclaw_memory",
    # ⚠️ 教学 demo 默认值，仅限本地开发。生产环境必须通过环境变量注入
)

QWEN_API_KEY  = os.getenv("QWEN_API_KEY", "")
EMBED_MODEL   = "text-embedding-v3"       # 通义中文优化 embedding
EMBED_DIM     = 1024
# 提取摘要+标签的模型。
# 课程设计原本建议使用轻量模型（如 qwen3-turbo）以控制成本；
# 考虑到部分环境未开通 turbo，为保证 demo 可跑通，这里默认使用 qwen3-max。
EXTRACT_MODEL = "qwen3-max"

# 通义 embedding API（兼容 OpenAI SDK）
_embed_client = OpenAI(
    api_key  = QWEN_API_KEY,
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 通义 LLM（提取摘要+标签）
_llm_client = OpenAI(
    api_key  = QWEN_API_KEY,
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ─────────────────────────────────────────────────────────────────────────────
# Step 1：解析 session JSONL → 轮次列表
# ─────────────────────────────────────────────────────────────────────────────

def parse_turns(jsonl_path: Path) -> list[dict[str, Any]]:
    """
    解析 session JSONL，按 user+assistant 配对切轮次。
    💡 核心点：一轮对话 = 语义完整的最小 chunk 单元
    """
    lines = [
        json.loads(line)
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # 读取 meta 行
    meta = next((l for l in lines if l.get("type") == "meta"), {})
    routing_key = meta.get("routing_key", "unknown")
    session_id  = meta.get("session_id",  jsonl_path.stem)

    # 按 user+assistant 配对
    turns = []
    messages = [l for l in lines if l.get("type") == "message"]
    i = 0
    while i < len(messages):
        if messages[i].get("role") == "user":
            user_msg = messages[i]
            asst_msg = messages[i + 1] if i + 1 < len(messages) and messages[i + 1].get("role") == "assistant" else None
            if asst_msg:
                turns.append({
                    "session_id":      session_id,
                    "routing_key":     routing_key,
                    "user_message":    user_msg.get("content", ""),
                    "assistant_reply": asst_msg.get("content", ""),
                    # 💡 ts 统一转为毫秒整数；兼容 ISO 字符串（m3l20 写入格式）和整数（XiaoPaw 原生格式）
                    "turn_ts":         int(user_msg.get("ts", 0)) if str(user_msg.get("ts", "0")).isdigit() else 0,
                })
                i += 2
                continue
        i += 1

    return turns
# ─────────────────────────────────────────────────────────────────────────────
# Step 2：LLM 提取摘要 + 标签
# ─────────────────────────────────────────────────────────────────────────────
_EXTRACT_PROMPT = """\
分析以下一轮对话，提取结构化信息，以 JSON 格式返回：

{{
  "summary": "一句话摘要，描述这轮对话做了什么（20字以内）",
  "tags": ["标签1", "标签2"]  // 2-4个领域标签，如：工作、文件处理、日程、搜索、代码等
}}

只返回 JSON，不要其他内容。

用户：{user_message}
助手：{assistant_reply}
"""

def extract_summary_and_tags(user_message: str, assistant_reply: str) -> tuple[str, list[str]]:
    """
    💡 核心点：每轮只调用一次模型，做结构化提取（摘要 + 标签）
    默认模型为 qwen3-max（兼容性优先）；如环境支持，可切换轻量模型以节省成本
    """
    prompt = _EXTRACT_PROMPT.format(
        user_message    = user_message[:500],    # 截断防止超长
        assistant_reply = assistant_reply[:500],
    )
    resp = _llm_client.chat.completions.create(
        model    = EXTRACT_MODEL,
        messages = [{"role": "user", "content": prompt}],
        extra_body={"enable_thinking": False},   # turbo 模型关闭思考链，节省 token
    )
    raw = resp.choices[0].message.content.strip()

    # 清理可能的 markdown 代码块
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()  # 兜底：去掉前导换行和空白

    try:
        data = json.loads(raw)
        return data.get("summary", ""), data.get("tags", [])
    except json.JSONDecodeError:
        return user_message[:50], []

# ─────────────────────────────────────────────────────────────────────────────
# Step 3：向量化
# ─────────────────────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    批量向量化，返回 float[] 列表。
    💡 核心点：summary 和 message 分别向量化，支持不同维度的语义搜索
    """
    resp = _embed_client.embeddings.create(
        model      = EMBED_MODEL,
        input      = texts,
        dimensions = EMBED_DIM,
    )
    return [item.embedding for item in resp.data]

# ─────────────────────────────────────────────────────────────────────────────
# Step 4：写入 pgvector
# ─────────────────────────────────────────────────────────────────────────────

def upsert_memory(conn: Any, record: dict[str, Any]) -> None:
    """
    写入一条记忆记录，id 相同时跳过（幂等）。
    💡 核心点：search_text = user_message + tags 拼接，供全文索引使用
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memories (
                id, session_id, routing_key,
                user_message, assistant_reply,
                summary, tags,
                turn_ts,
                summary_vec, message_vec,
                search_text
            ) VALUES (
                %(id)s, %(session_id)s, %(routing_key)s,
                %(user_message)s, %(assistant_reply)s,
                %(summary)s, %(tags)s,
                %(turn_ts)s,
                %(summary_vec)s::vector, %(message_vec)s::vector,
                %(search_text)s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            {
                **record,
                "summary_vec": str(record["summary_vec"]),
                "message_vec": str(record["message_vec"]),
            },
        )
    conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# 主入口：index_session（同步版，供 demo 调用）
# ─────────────────────────────────────────────────────────────────────────────
def index_session(jsonl_path: Path) -> int:
    """
    对一个 session JSONL 完整建索引，返回写入条数。
    """
    turns = parse_turns(jsonl_path)
    if not turns:
        return 0

    conn = psycopg2.connect(DB_DSN)
    written = 0

    try:
        for turn in turns:
            # 生成稳定 id（session_id + turn_ts + user_message 前32字符）
            raw_id = f"{turn['session_id']}_{turn['turn_ts']}_{turn['user_message'][:32]}"
            turn_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

            # 检查是否已存在（幂等）
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM memories WHERE id = %s", (turn_id,))
                if cur.fetchone():
                    continue

            # Step 2：提取摘要 + 标签
            summary, tags = extract_summary_and_tags(
                turn["user_message"], turn["assistant_reply"]
            )

            # Step 3：向量化（摘要 + 原始对话拼接）
            message_text = f"用户：{turn['user_message']}\n助手：{turn['assistant_reply']}"
            vecs = embed_texts([summary, message_text])

            # Step 4：写入
            search_text = turn["user_message"] + " " + " ".join(tags)
            upsert_memory(conn, {
                "id":              turn_id,
                "session_id":      turn["session_id"],
                "routing_key":     turn["routing_key"],
                "user_message":    turn["user_message"],
                "assistant_reply": turn["assistant_reply"],
                "summary":         summary,
                "tags":            tags,
                "turn_ts":         turn["turn_ts"],
                "summary_vec":     vecs[0],
                "message_vec":     vecs[1],
                "search_text":     search_text,
            })
            written += 1
            print(f"  ✓ 已索引：{summary[:40]}  tags={tags}")
    finally:
        conn.close()

    return written


# ─────────────────────────────────────────────────────────────────────────────
# 异步包装（供 XiaoPawCrew 每轮对话后后台触发）
# ─────────────────────────────────────────────────────────────────────────────
async def async_index_turn(
    session_id:      str,
    routing_key:     str,
    user_message:    str,
    assistant_reply: str,
    turn_ts:         int,
) -> None:
    """
    💡 核心点：异步化，每轮对话结束后 asyncio.create_task() 触发，不阻塞主流程
    """
    await asyncio.get_running_loop().run_in_executor(
        None,
        _index_single_turn,
        session_id, routing_key, user_message, assistant_reply, turn_ts,
    )


def _index_single_turn(
    session_id:      str,
    routing_key:     str,
    user_message:    str,
    assistant_reply: str,
    turn_ts:         int,
) -> None:
    raw_id  = f"{session_id}_{turn_ts}_{user_message[:32]}"
    turn_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM memories WHERE id = %s", (turn_id,))
            if cur.fetchone():
                return  # 已存在，跳过

        summary, tags = extract_summary_and_tags(user_message, assistant_reply)
        message_text  = f"用户：{user_message}\n助手：{assistant_reply}"
        vecs          = embed_texts([summary, message_text])
        search_text   = user_message + " " + " ".join(tags)

        upsert_memory(conn, {
            "id":              turn_id,
            "session_id":      session_id,
            "routing_key":     routing_key,
            "user_message":    user_message,
            "assistant_reply": assistant_reply,
            "summary":         summary,
            "tags":            tags,
            "turn_ts":         turn_ts,
            "summary_vec":     vecs[0],
            "message_vec":     vecs[1],
            "search_text":     search_text,
        })
    finally:
        conn.close()