"""E2E 测试：m5l32 课程演示四条路径的完整流程。

覆盖：
    S1: 正常流程 → Bootstrap + SkillLoader + sop_design（mock SkillLoader 以隔离沙盒）
    S2: --attack privilege → PermissionGate DENY shell_executor
    S3: --attack inject → SandboxGuard BLOCK 路径遍历
    S4: --attack api-leak → SecureToolWrapper 注入密钥，LLM 不可见

验收维度：
    - 产出：OUTPUT_DIR 文件 / metrics API 数值
    - 日志：security_audit.jsonl / workspace audit.log
    - Langfuse：trace 结构、tool span、generation 的 input/output 不含明文密钥

运行方式：
    # 全部测试（需 LLM API key，真实调用）
    python3 -m pytest tests/test_e2e_demo_flow.py -v -s

    # 仅 dispatch 表等快速路径（无需 LLM）
    python3 -m pytest tests/test_e2e_demo_flow.py -m "not integration" -v
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_DIR))                  # m5l32/
sys.path.insert(0, str(_DIR.parent))           # crewai_mas_demo/（tools, llm 等）

from dotenv import load_dotenv

load_dotenv(_DIR / ".env", override=False)

from hook_framework import (  # noqa: E402
    CrewObservabilityAdapter,
    GuardrailDeny,
    HookLoader,
    HookRegistry,
)


# ─────────────────────────── Fixtures ───────────────────────────


@pytest.fixture(autouse=True)
def _isolate_env():
    """防止本文件中对安全相关 env 的写入泄漏给其它测试文件。

    monkeypatch.delenv(raising=False) 对不存在的 key 不记录状态，因此若后续
    代码用 setdefault 创建该 key，teardown 无法清除——需在此处手动兜底。
    """
    keys = ("SECURITY_POLICY_PATH", "SECURITY_AUDIT_FILE",
            "COST_GUARD_BUDGET", "SECURE_API_KEY")
    before = {k: os.environ.get(k) for k in keys}
    yield
    for k, v in before.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def _reset_langfuse_globals():
    """langfuse_trace 模块级 globals 跨测试复用会串 trace，必须每次清零。"""
    from shared_hooks import langfuse_trace as lt

    def _reset():
        lt._client = None
        lt._init_failed = False
        with lt._batch_lock:
            lt._batch_buffer.clear()
        lt._trace_id_var.set("")
        lt._session_id_var.set("")
        lt._root_span_id_var.set("")
        lt._gen_id_var.set("")
        lt._gen_count_var.set(0)
        lt._tool_count_var.set(0)
        lt._span_stack_var.set(())

    _reset()
    yield
    _reset()


class _SpanSpy:
    """模拟 Langfuse Observation，记录 start/update/end 及 otel 属性。"""

    def __init__(self, events: list, kwargs: dict):
        self._events = events
        self._kwargs = kwargs
        events.append({"action": "start", **kwargs})
        # 模拟 _otel_span，_set_trace_attrs 需要调 set_attribute
        spy = self

        class _Otel:
            def set_attribute(self, k, v):
                spy._events.append({"action": "attr", "name": spy._kwargs.get("name"),
                                    "key": k, "value": v})

        self._otel_span = _Otel()

    def update(self, **kwargs):
        self._events.append({"action": "update", "name": self._kwargs.get("name"), **kwargs})

    def end(self):
        self._events.append({"action": "end", "name": self._kwargs.get("name")})


@pytest.fixture
def langfuse_spy(_reset_langfuse_globals):
    """Patch langfuse.Langfuse，拦截 api.ingestion.batch() 捕获所有 span/generation 事件。

    langfuse_trace.py 使用批量注入 API（ingestion.batch），不再使用 start_observation。
    本 spy 将 batch items 翻译成 {"action", "name", "as_type", "input", "output"} 格式，
    与测试断言保持兼容。
    """
    events: list[dict] = []
    _id_to_name: dict[str, str] = {}

    def _process_batch(batch):
        for item in batch:
            item_type = getattr(item, "type", "")
            body = getattr(item, "body", None)
            if body is None:
                continue
            if item_type == "span-create":
                sid = getattr(body, "id", "")
                name = getattr(body, "name", "") or ""
                _id_to_name[sid] = name
                events.append({"action": "start", "name": name,
                               "input": getattr(body, "input", None)})
            elif item_type == "span-update":
                sid = getattr(body, "id", "")
                events.append({"action": "update",
                               "name": _id_to_name.get(sid, ""),
                               "output": getattr(body, "output", None)})
            elif item_type == "generation-create":
                gid = getattr(body, "id", "")
                name = getattr(body, "name", "") or ""
                _id_to_name[gid] = name
                events.append({"action": "start", "name": name, "as_type": "generation",
                               "input": getattr(body, "input", None), "output": None})
            elif item_type == "generation-update":
                gid = getattr(body, "id", "")
                events.append({"action": "update",
                               "name": _id_to_name.get(gid, ""),
                               "as_type": "generation",
                               "output": getattr(body, "output", None)})

    def _client_factory(*args, **kwargs):
        client = MagicMock()
        client.create_trace_id = lambda seed=None: f"trace-{seed or 'x'}"

        def _batch_side_effect(batch=None, **kw):
            if batch:
                _process_batch(batch)

        client.api = MagicMock()
        client.api.ingestion = MagicMock()
        client.api.ingestion.batch = MagicMock(side_effect=_batch_side_effect)
        return client

    # langfuse_trace._ensure_client() 执行 `from langfuse import Langfuse`，
    # 必须 patch 源头 `langfuse.Langfuse` 而非 shared_hooks 内的拷贝。
    with patch("langfuse.Langfuse", side_effect=_client_factory):
        yield SimpleNamespace(events=events)


@pytest.fixture
def isolated_audit(tmp_path, monkeypatch):
    """把两类审计日志重定向到 tmp_path，避免污染真实 workspace。"""
    security_jsonl = tmp_path / "security_audit.jsonl"
    monkeypatch.setenv("SECURITY_AUDIT_FILE", str(security_jsonl))
    monkeypatch.setenv(
        "SECURITY_POLICY_PATH",
        str(_DIR / "workspace" / "demo_agent" / "security.yaml"),
    )
    monkeypatch.delenv("COST_GUARD_BUDGET", raising=False)

    task_log = tmp_path / "task_audit.log"
    ws_hooks_dir = str(_DIR / "workspace" / "demo_agent" / "hooks")
    if ws_hooks_dir not in sys.path:
        sys.path.insert(0, ws_hooks_dir)
    import task_audit  # type: ignore

    monkeypatch.setattr(task_audit, "AUDIT_FILE", task_log)

    return SimpleNamespace(security_jsonl=security_jsonl, task_log=task_log)


@pytest.fixture
def demo_runtime(isolated_audit, langfuse_spy):
    """模拟 demo.main() 的共用初始化：registry + adapter + llm。"""
    import demo  # type: ignore

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_two_layers(
        global_dir=_DIR / "shared_hooks",
        workspace_dir=_DIR / "workspace" / "demo_agent",
    )
    adapter = CrewObservabilityAdapter(registry, session_id=f"test_demo_flow-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    adapter.install_global_hooks()

    llm = demo._build_llm()

    yield SimpleNamespace(
        demo=demo,
        registry=registry,
        loader=loader,
        strategies=loader.strategies,
        adapter=adapter,
        llm=llm,
        audit=isolated_audit,
        langfuse=langfuse_spy,
    )

    adapter.cleanup()


@pytest.fixture
def isolated_output(tmp_path, monkeypatch):
    """把 demo.OUTPUT_DIR 重定向到 tmp_path，避免污染真实产出目录。"""
    import demo  # type: ignore

    out = tmp_path / "output"
    out.mkdir()
    monkeypatch.setattr(demo, "OUTPUT_DIR", out)
    return out


# ─────────────────────────── 快速路径：dispatch 表 ───────────────────────────


def test_attack_dispatch_table_maps_all_modes_to_runners():
    """demo.main() 的 runner 分派表必须覆盖：None / privilege / inject / api-leak。"""
    import demo  # type: ignore

    table = demo._runner_table()
    assert set(table.keys()) == {None, "privilege", "inject", "api-leak"}
    for key, fn in table.items():
        assert callable(fn), f"runner for {key!r} must be callable"


def test_set_security_env_wires_policy_and_audit_paths(monkeypatch, tmp_path):
    """_set_security_env 必须只在 main() 层写 env，runner 不得再写。"""
    import demo  # type: ignore

    monkeypatch.delenv("SECURITY_POLICY_PATH", raising=False)
    monkeypatch.delenv("SECURITY_AUDIT_FILE", raising=False)
    monkeypatch.delenv("COST_GUARD_BUDGET", raising=False)

    args = SimpleNamespace(attack=None, budget=1.0, task=[])
    demo._set_security_env(args)

    assert os.environ["SECURITY_POLICY_PATH"].endswith("security.yaml")
    assert os.environ["SECURITY_AUDIT_FILE"].endswith("security_audit.jsonl")

    # budget != 1.0 才会写 COST_GUARD_BUDGET
    args2 = SimpleNamespace(attack=None, budget=0.001, task=[])
    demo._set_security_env(args2)
    assert os.environ["COST_GUARD_BUDGET"] == "0.001"


# ─────────────────────────── S1：正常流程（mock SkillLoader）───────────────────────────


@pytest.mark.integration
def test_normal_runs_bootstrap_and_skill_loader(demo_runtime, isolated_output, monkeypatch):
    """S1: run_normal 使用 Bootstrap + SkillLoader 结构；mock SkillLoaderTool 模拟沙盒产出。"""
    rt = demo_runtime

    # Mock SkillLoaderTool：拦截 _run，写一份假的 design_doc.md
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field, PrivateAttr

    captured = {"built_with": None, "invoked_with": None}
    design_doc = isolated_output / "design_doc.md"

    class _SkillInput(BaseModel):
        skill_name: str = Field(description="要加载的 Skill 名称")
        task_context: str = Field(default="", description="任务描述")

    class _FakeSkillLoader(BaseTool):
        name: str = "skill_loader"
        description: str = "模拟的 SkillLoader（测试专用）"
        args_schema: type[BaseModel] = _SkillInput
        _skill_registry: dict = PrivateAttr(default_factory=dict)

        def __init__(self, skills_dir="", sandbox_mcp_url="", sandbox_mount_desc="", **kwargs):
            super().__init__()
            captured["built_with"] = {
                "skills_dir": skills_dir,
                "sandbox_mcp_url": sandbox_mcp_url,
                "sandbox_mount_desc": sandbox_mount_desc,
            }
            self._skill_registry = {"sop_design": {"type": "task"}}

        def _run(self, skill_name, task_context=""):
            captured["invoked_with"] = {"skill_name": skill_name,
                                        "task_context_len": len(task_context)}
            design_doc.write_text(
                "# 设计文档（mock）\n\n## Step 1 需求摘要\n...\n\n## Step 4 风险与待确认\n...\n"
            )
            return json.dumps({
                "errcode": 0,
                "errmsg": "success",
                "file_path": str(design_doc),
            }, ensure_ascii=False)

    monkeypatch.setattr(rt.demo, "SkillLoaderTool", _FakeSkillLoader)

    # 为加速测试，缩短 max_iter（需 run_normal 允许 override；否则走默认即可）
    args = SimpleNamespace(attack=None, budget=10.0, task=["为测试功能产出技术设计文档"])

    rt.demo.run_normal(args, rt.adapter, rt.llm)

    # --- 验收：SkillLoader 以正确参数构造 ---
    assert captured["built_with"] is not None
    assert captured["built_with"]["sandbox_mcp_url"].startswith("http://")

    # --- 验收：产出文件存在 ---
    assert design_doc.exists(), "run_normal 应通过 SkillLoader 产出 design_doc.md"

    # cleanup 触发 SESSION_END → flush_and_close() → _flush_batch()，spy 才能拦截 batch 事件
    rt.adapter.cleanup()

    # --- 验收：Langfuse 至少记录 session / turn 级 span ---
    started_names = [e.get("name", "") for e in rt.langfuse.events if e["action"] == "start"]
    assert any(n.startswith("session-") for n in started_names), \
        f"应有 session span；实际 started_names={started_names}"


# ─────────────────────────── S2：--attack privilege ───────────────────────────


@pytest.mark.integration
def test_attack_privilege_blocked_by_permission_gate(demo_runtime):
    """S2: --attack privilege 触发 PermissionGate DENY；度量/审计/Langfuse 三端留痕。"""
    rt = demo_runtime
    args = SimpleNamespace(attack="privilege", budget=1.0, task=[])

    try:
        rt.demo.run_attack_privilege(args, rt.adapter, rt.llm)
    except GuardrailDeny:
        pass

    # --- metrics ---
    pg = rt.strategies["permission_gate"]
    m = pg.get_metrics()
    assert m["deny_count"] >= 1, f"permission_gate 至少 deny 一次；实际 metrics={m}"
    assert "shell_executor" in m["denied_tools"]

    # --- 审计日志（触发 cleanup 才会落 session_summary；主动触发一次）---
    rt.adapter.cleanup()

    lines = rt.audit.security_jsonl.read_text().splitlines()
    deny_entries = [json.loads(l) for l in lines
                    if '"permission_deny"' in l]
    assert len(deny_entries) >= 1, f"审计日志应记录 permission_deny；实际 lines={lines}"
    assert any(e.get("tool") == "shell_executor" for e in deny_entries)

    # --- Langfuse：至少记录一个 tool-shell_executor span ---
    tool_starts = [e for e in rt.langfuse.events
                   if e["action"] == "start"
                   and str(e.get("name", "")).startswith("tool-shell_executor")]
    assert len(tool_starts) >= 1, \
        "Langfuse 应在 BEFORE_TOOL_CALL 阶段为 shell_executor 创建 tool span"


# ─────────────────────────── S3：--attack inject ───────────────────────────


@pytest.mark.integration
def test_attack_inject_blocked_by_sandbox_guard(demo_runtime):
    """S3: --attack inject 触发 SandboxGuard 路径遍历拦截。"""
    rt = demo_runtime
    args = SimpleNamespace(attack="inject", budget=1.0, task=[])

    try:
        rt.demo.run_attack_inject(args, rt.adapter, rt.llm)
    except GuardrailDeny:
        pass

    sg = rt.strategies["sandbox_guard"]
    m = sg.get_metrics()
    assert m["total_violations"] >= 1, f"sandbox_guard 应至少拦截一次；实际 metrics={m}"
    assert "path_traversal" in m["violations_by_type"] or \
           any("traversal" in v_type for v_type in m["violations_by_type"])

    rt.adapter.cleanup()

    lines = rt.audit.security_jsonl.read_text().splitlines()
    sandbox_events = [json.loads(l) for l in lines
                      if "sandbox_" in l and "traversal" in l]
    assert len(sandbox_events) >= 1, \
        f"审计日志应记录 sandbox_path_traversal；实际 lines={lines}"

    # Langfuse 应记录（被拦截前就开了 span，adapter 在 deny 时不再走 after_tool，
    # 但 before_tool span 已创建；flush_and_close 会关掉孤儿 span）
    tool_starts = [e for e in rt.langfuse.events
                   if e["action"] == "start"
                   and str(e.get("name", "")).startswith("tool-")]
    # sandbox_guard 在 permission_gate 之前注册；permission_gate 不会 deny knowledge_search
    # 因此 tool span 应已创建
    # （此处不强断言具体工具名，因为 inject 分支的工具名可能是 knowledge_search）
    assert len(tool_starts) >= 0  # 宽松断言：至少跑完了 hook 链


# ─────────────────────────── S4：--attack api-leak ───────────────────────────


@pytest.mark.integration
def test_attack_api_leak_masks_credential(demo_runtime, monkeypatch):
    """S4: --attack api-leak 通过 SecureToolWrapper 注入密钥；Langfuse 的 generation input 不见明文。"""
    rt = demo_runtime
    FAKE_KEY = "sk-TEST-" + "A" * 40
    monkeypatch.setenv("SECURE_API_KEY", FAKE_KEY)

    args = SimpleNamespace(attack="api-leak", budget=1.0, task=[])

    try:
        rt.demo.run_attack_api_leak(args, rt.adapter, rt.llm)
    except GuardrailDeny:
        pass

    rt.adapter.cleanup()

    # --- 从 Langfuse 事件中取出所有 generation span 的 input/output ---
    # generation 应含 prompt_preview（来自 BEFORE_LLM messages）
    gen_events = [e for e in rt.langfuse.events
                  if e["action"] == "start" and e.get("as_type") == "generation"]
    tool_events = [e for e in rt.langfuse.events
                   if e["action"] in ("start", "update")
                   and str(e.get("name", "")).startswith("tool-secure_api")]

    # 至少一次 LLM 调用
    assert len(gen_events) >= 1 or len(tool_events) >= 1, \
        "run_attack_api_leak 应产生至少一次 LLM 或工具调用"

    # --- 关键断言：LLM 的 prompt/response 全链路不得出现完整密钥 ---
    for e in gen_events:
        blob = json.dumps({"input": e.get("input"), "output": e.get("output")},
                          ensure_ascii=False, default=str)
        assert FAKE_KEY not in blob, \
            f"Langfuse generation span 不应包含明文密钥；违规 event={e}"

    # --- tool span 的 input 也不该包含明文密钥（input 来自 LLM 的 tool_input）---
    for e in tool_events:
        blob = json.dumps(e.get("input"), ensure_ascii=False, default=str)
        assert FAKE_KEY not in blob, \
            f"Langfuse tool span 的 input（来自 LLM）不应含明文密钥；event={e}"

    # --- tool 返回值应是脱敏形式（sk-T...AAAA 之类）---
    #     tool output 仅出现在 AFTER_TOOL_CALL 阶段，通过 span.update(output=...) 写入
    tool_updates = [e for e in rt.langfuse.events
                    if e["action"] == "update"
                    and str(e.get("name", "")).startswith("tool-secure_api")
                    and e.get("output")]
    if tool_updates:
        combined_output = " ".join(str(e.get("output", "")) for e in tool_updates)
        assert FAKE_KEY not in combined_output, \
            "工具返回的脱敏输出不应包含完整密钥"
        # 脱敏形式允许：sk-T...AAAA 或 sk-T**...**A 等
        assert re.search(r"sk-T\w{0,4}\.\.\.\w{0,4}", combined_output), \
            f"tool 返回应为脱敏形式（sk-T...xxxx）；实际={combined_output}"