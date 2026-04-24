"""
第23课 单元测试：Orchestrator 范式

测试覆盖：
  T1 - spawn_sub_agent 完成后 output_file 存在且非空
  T2 - spawn_sub_agents_parallel 并发产出两个文件，wall time < 串行时间之和
  T3 - tool_names 包含未知工具名时静默过滤，不报错
  T4 - _run_one_sub_crew 内部异常时返回 error 字符串（parallel 场景）
  T5 - 并发任务一个失败，其他正常完成
  T6 - SOP skill 文件存在且可读
  T7 - 主 Agent backstory 包含 SOP 内容
  T8 - 两个并发 sub-crew 使用不同的 Crew 实例（上下文隔离）

运行：
  cd m4l23~28/m4l23 && pytest test_orchestrator.py -v
"""
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HERE))

from m4_23_orchestrator import (  # noqa: E402
    SKILL_PATH,
    TOOL_REGISTRY,
    WORKSPACE_DIR,
    SpawnParallelTool,
    SpawnSubAgentTool,
    _run_one_sub_crew,
    build_orchestrator,
    load_sop_skill,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_output(tmp_path) -> Path:
    return tmp_path / "output.md"



def _mock_sub_crew(output_file: str, content: str = "mock output") -> None:
    """让 _run_one_sub_crew 直接写文件，跳过 LLM 调用"""
    p = Path(output_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# T1：spawn_sub_agent 完成后文件存在且非空
# ─────────────────────────────────────────────────────────────────────────────

def test_T1_spawn_sub_agent_creates_file(tmp_path):
    output_file = str(tmp_path / "result.md")

    with patch("m4_23_orchestrator._run_one_sub_crew") as mock_run:
        mock_run.side_effect = lambda **kwargs: _mock_sub_crew(
            kwargs["output_file"], "# 测试输出\n内容"
        ) or kwargs["output_file"]

        tool = SpawnSubAgentTool()
        result = tool._run(
            role="Test Agent",
            goal="测试目标",
            task="写一个测试文件",
            context="测试上下文",
            tool_names="FileWriterTool",
            output_file=output_file,
        )
    print(f"output_file from tool: {output_file}")
    assert Path(output_file).exists(), "output_file 应该存在"
    assert Path(output_file).read_text() != "", "output_file 不应为空"
    assert result == output_file

# ─────────────────────────────────────────────────────────────────────────────
# T2：并发产出两个文件，wall time < 各自串行时间之和
# ─────────────────────────────────────────────────────────────────────────────

def test_T2_parallel_concurrent_faster_than_serial(tmp_path):
    delay = 0.3  # 每个子任务模拟 0.3s

    def slow_sub_crew(**kwargs):
        time.sleep(delay)
        _mock_sub_crew(kwargs["output_file"], "output")
        return kwargs["output_file"]

    subtasks = [
        {"role": "Agent A", "goal": "g", "task": "t", "context": "c",
         "tool_names": "FileWriterTool", "output_file": str(tmp_path / "a.md")},
        {"role": "Agent B", "goal": "g", "task": "t", "context": "c",
         "tool_names": "FileWriterTool", "output_file": str(tmp_path / "b.md")},
    ]

    with patch("m4l23_orchestrator._run_one_sub_crew", side_effect=lambda **kw: slow_sub_crew(**kw)):
        tool = SpawnParallelTool()
        start = time.time()
        result_json = tool._run(json.dumps(subtasks))
        elapsed = time.time() - start

    results = json.loads(result_json)
    assert Path(tmp_path / "a.md").exists()
    assert Path(tmp_path / "b.md").exists()
    # 并发应比串行（2 * delay）快
    assert elapsed < delay * 2 * 0.9, f"并发用时 {elapsed:.2f}s 不应接近串行 {delay * 2:.2f}s"
