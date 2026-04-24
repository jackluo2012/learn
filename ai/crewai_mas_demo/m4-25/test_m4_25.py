"""
第25课 集成测试 - test_m4l25.py

测试策略：
  - T1-T2：结构完整性测试（无 API，验证 workspace/skills 文件正确）
  - T3-T4：Bootstrap 加载测试（无 API，验证 build_bootstrap_prompt 正确注入）
  - T5-T6：边界规则测试（无 API，验证 soul.md 中 NEVER 清单存在且完整）
  - T7：SOP Skills 完整性
  - T8：Demo 输入文件
  - T-V2a/b：Memory 隔离 + 四层框架完整性
  - T-Generic：DigitalWorkerCrew 通用框架验证
  - T_E2E：真实执行测试（需 Docker 沙盒 + LLM API）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_M4L25_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L25_DIR.parent
for _p in [str(_M4L25_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from m3_20.m3_20_file_memory import build_bootstrap_prompt  # noqa: E402

WORKSPACE_MANAGER = _M4L25_DIR / "workspace" / "manager"
WORKSPACE_DEV = _M4L25_DIR / "workspace" / "dev"
# 💡 v3：skills 已移入各角色 workspace 内部（数字员工的能力完全由 Workspace 决定）
MANAGER_SKILLS_DIR = WORKSPACE_MANAGER / "skills"
DEV_SKILLS_DIR = WORKSPACE_DEV / "skills"


# ── T1 | Manager workspace 四件套 ───────────────────────────────────────────

class TestT1ManagerWorkspaceStructure:

    @pytest.mark.parametrize("filename", ["soul.md", "user.md", "agent.md", "memory.md"])
    def test_workspace_files_exist(self, filename: str) -> None:
        path = WORKSPACE_MANAGER / filename
        assert path.exists(), f"Manager workspace 缺少 {filename}"

    def test_soul_md_not_empty(self) -> None:
        content = (WORKSPACE_MANAGER / "soul.md").read_text(encoding="utf-8")
        assert len(content.strip()) > 100, "soul.md 内容过少"

    def test_agent_md_contains_team_roster(self) -> None:
        content = (WORKSPACE_MANAGER / "agent.md").read_text(encoding="utf-8")
        assert "PM" in content, "团队名册缺少 PM 角色"
        assert "Dev" in content, "团队名册缺少 Dev 角色"
        assert "QA" in content, "团队名册缺少 QA 角色"


# ── T2 | Dev workspace 四件套 ────────────────────────────────────────────────

class TestT2DevWorkspaceStructure:

    @pytest.mark.parametrize("filename", ["soul.md", "user.md", "agent.md", "memory.md"])
    def test_workspace_files_exist(self, filename: str) -> None:
        path = WORKSPACE_DEV / filename
        assert path.exists(), f"Dev workspace 缺少 {filename}"

    def test_agent_md_contains_boundary_table(self) -> None:
        content = (WORKSPACE_DEV / "agent.md").read_text(encoding="utf-8")
        assert "我负责" in content or "负责" in content, "Dev agent.md 缺少职责边界"
        assert "Manager" in content, "Dev agent.md 缺少汇报对象（Manager）"

    def test_agent_md_team_position(self) -> None:
        content = (WORKSPACE_DEV / "agent.md").read_text(encoding="utf-8")
        assert "PM" in content, "Dev agent.md 未说明上游角色 PM"
        assert "QA" in content, "Dev agent.md 未说明下游角色 QA"


# ── T3 | Manager bootstrap prompt ───────────────────────────────────────────

class TestT3ManagerBootstrap:

    def setup_method(self) -> None:
        self.prompt = build_bootstrap_prompt(WORKSPACE_MANAGER)

    def test_contains_soul_tag(self) -> None:
        assert "<soul>" in self.prompt

    def test_contains_user_profile_tag(self) -> None:
        assert "<user_profile>" in self.prompt

    def test_contains_agent_rules_tag(self) -> None:
        assert "<agent_rules>" in self.prompt

    def test_contains_memory_index_tag(self) -> None:
        assert "<memory_index>" in self.prompt

    def test_team_roster_in_prompt(self) -> None:
        assert "PM" in self.prompt and "Dev" in self.prompt and "QA" in self.prompt


# ── T4 | Dev bootstrap prompt ────────────────────────────────────────────────

class TestT4DevBootstrap:

    def setup_method(self) -> None:
        self.prompt = build_bootstrap_prompt(WORKSPACE_DEV)

    def test_contains_soul_tag(self) -> None:
        assert "<soul>" in self.prompt

    def test_soul_contains_dev_identity(self) -> None:
        assert "Dev" in self.prompt or "开发工程师" in self.prompt

    def test_contains_boundary_content(self) -> None:
        assert "Manager" in self.prompt


# ── T5 | Manager NEVER rules ────────────────────────────────────────────────

class TestT5ManagerNeverRules:

    def setup_method(self) -> None:
        self.soul = (WORKSPACE_MANAGER / "soul.md").read_text(encoding="utf-8")

    def test_never_section_exists(self) -> None:
        assert "NEVER" in self.soul or "禁止" in self.soul

    def test_never_write_code(self) -> None:
        assert "代码" in self.soul

    def test_never_modify_requirement(self) -> None:
        assert "需求" in self.soul

    def test_deliverable_format_defined(self) -> None:
        assert "task_breakdown" in self.soul


# ── T6 | Dev NEVER rules ────────────────────────────────────────────────────

class TestT6DevNeverRules:

    def setup_method(self) -> None:
        self.soul = (WORKSPACE_DEV / "soul.md").read_text(encoding="utf-8")

    def test_never_section_exists(self) -> None:
        assert "NEVER" in self.soul or "禁止" in self.soul

    def test_never_modify_requirement(self) -> None:
        assert "需求" in self.soul

    def test_never_skip_design(self) -> None:
        assert "技术设计" in self.soul or "tech_design" in self.soul

    def test_deliverable_format_defined(self) -> None:
        assert "tech_design" in self.soul


# ── T7 | SOP Skills 完整性（v3：workspace-local skills）────────────────────

class TestT7SopSkillsIntegrity:
    """
    v3 架构：Skills 从全局 crewai_mas_demo/skills/ 移入各角色 workspace 内部。
    核心原则：数字员工的能力完全由 Workspace 决定。
    """

    def test_manager_sop_skill_exists(self) -> None:
        """Manager workspace 内部有 sop_manager skill"""
        assert (MANAGER_SKILLS_DIR / "sop_manager" / "SKILL.md").exists(), \
            "workspace/manager/skills/sop_manager/SKILL.md 不存在"

    def test_dev_sop_skill_exists(self) -> None:
        """Dev workspace 内部有 sop_dev skill"""
        assert (DEV_SKILLS_DIR / "sop_dev" / "SKILL.md").exists(), \
            "workspace/dev/skills/sop_dev/SKILL.md 不存在"

    def test_manager_sop_has_steps(self) -> None:
        content = (MANAGER_SKILLS_DIR / "sop_manager" / "SKILL.md").read_text(encoding="utf-8")
        assert "步骤" in content or "Step" in content
        assert "task_breakdown" in content

    def test_dev_sop_has_steps(self) -> None:
        content = (DEV_SKILLS_DIR / "sop_dev" / "SKILL.md").read_text(encoding="utf-8")
        assert "步骤" in content or "Step" in content
        assert "tech_design" in content

    def test_manager_load_skills_yaml_exists(self) -> None:
        """Manager workspace 有 load_skills.yaml，注册了 sop_manager（reference 类型）"""
        yaml_content = (MANAGER_SKILLS_DIR / "load_skills.yaml").read_text(encoding="utf-8")
        assert "sop_manager" in yaml_content
        assert "reference" in yaml_content

    def test_dev_load_skills_yaml_exists(self) -> None:
        """Dev workspace 有 load_skills.yaml，注册了 sop_dev（reference 类型）"""
        yaml_content = (DEV_SKILLS_DIR / "load_skills.yaml").read_text(encoding="utf-8")
        assert "sop_dev" in yaml_content
        assert "reference" in yaml_content

    def test_manager_sop_is_reference_type(self) -> None:
        yaml_content = (MANAGER_SKILLS_DIR / "load_skills.yaml").read_text(encoding="utf-8")
        lines = yaml_content.split("\n")
        in_sop_manager = False
        for line in lines:
            if "sop_manager" in line:
                in_sop_manager = True
            if in_sop_manager and "type:" in line:
                assert "reference" in line
                break

    def test_skills_isolated_per_workspace(self) -> None:
        """两个 workspace 的 skills 目录互相独立（v3 架构：能力随 workspace 而定）"""
        assert MANAGER_SKILLS_DIR != DEV_SKILLS_DIR
        assert not (MANAGER_SKILLS_DIR / "sop_dev").exists(), \
            "Manager workspace 不应含 sop_dev skill"
        assert not (DEV_SKILLS_DIR / "sop_manager").exists(), \
            "Dev workspace 不应含 sop_manager skill"


# ── T8 | Demo 输入文件 ──────────────────────────────────────────────────────

class TestT8DemoInputFiles:

    DEMO_DIR = _M4L25_DIR / "demo_input"

    def test_project_requirement_exists(self) -> None:
        assert (self.DEMO_DIR / "project_requirement.md").exists()

    def test_feature_requirement_exists(self) -> None:
        assert (self.DEMO_DIR / "feature_requirement.md").exists()

    def test_project_requirement_has_dod(self) -> None:
        content = (self.DEMO_DIR / "project_requirement.md").read_text(encoding="utf-8")
        assert "验收标准" in content or "DoD" in content

    def test_feature_requirement_has_dod(self) -> None:
        content = (self.DEMO_DIR / "feature_requirement.md").read_text(encoding="utf-8")
        assert "验收标准" in content or "DoD" in content


# ── T-V2a | Memory 隔离 ─────────────────────────────────────────────────────

class TestTV2aMemoryIsolation:

    def test_memory_paths_are_different(self) -> None:
        assert WORKSPACE_MANAGER != WORKSPACE_DEV

    def test_both_have_independent_memory_file(self) -> None:
        assert (WORKSPACE_MANAGER / "memory.md").exists()
        assert (WORKSPACE_DEV / "memory.md").exists()


# ── T-V2b | 四层框架完整性 ──────────────────────────────────────────────────

class TestTV2bFourLayerAlignment:

    def test_manager_agent_md_has_role_charter(self) -> None:
        content = (WORKSPACE_MANAGER / "agent.md").read_text(encoding="utf-8")
        assert "Role Charter" in content

    def test_dev_agent_md_has_role_charter(self) -> None:
        content = (WORKSPACE_DEV / "agent.md").read_text(encoding="utf-8")
        assert "Role Charter" in content

    def test_manager_soul_has_soul_label(self) -> None:
        content = (WORKSPACE_MANAGER / "soul.md").read_text(encoding="utf-8")
        assert "Soul" in content

    def test_dev_soul_has_soul_label(self) -> None:
        content = (WORKSPACE_DEV / "soul.md").read_text(encoding="utf-8")
        assert "Soul" in content

    def test_manager_soul_has_never_clause(self) -> None:
        content = (WORKSPACE_MANAGER / "soul.md").read_text(encoding="utf-8")
        assert "NEVER" in content or "禁止" in content

    def test_dev_soul_has_never_clause(self) -> None:
        content = (WORKSPACE_DEV / "soul.md").read_text(encoding="utf-8")
        assert "NEVER" in content or "禁止" in content


# ── T-Generic | DigitalWorkerCrew 通用框架验证 ──────────────────────────────

class TestGenericFramework:
    """验证 DigitalWorkerCrew 用同一个类、不同 workspace 产生不同 backstory"""

    def test_import_digital_worker(self) -> None:
        from shared.digital_worker import DigitalWorkerCrew
        assert DigitalWorkerCrew is not None

    def test_universal_constants(self) -> None:
        from shared.digital_worker import UNIVERSAL_ROLE, UNIVERSAL_GOAL
        assert UNIVERSAL_ROLE == "数字员工"
        assert "背景信息" in UNIVERSAL_GOAL or "可用技能" in UNIVERSAL_GOAL

    def test_manager_worker_has_manager_backstory(self) -> None:
        from shared.digital_worker import DigitalWorkerCrew
        worker = DigitalWorkerCrew(
            workspace_dir=WORKSPACE_MANAGER,
            sandbox_port=8023,
        )
        agent = worker.worker_agent()
        assert "项目经理" in agent.backstory or "Manager" in agent.backstory
        assert agent.role == "数字员工"

    def test_dev_worker_has_dev_backstory(self) -> None:
        from shared.digital_worker import DigitalWorkerCrew
        worker = DigitalWorkerCrew(
            workspace_dir=WORKSPACE_DEV,
            sandbox_port=8024,
        )
        agent = worker.worker_agent()
        assert "开发工程师" in agent.backstory or "Dev" in agent.backstory
        assert agent.role == "数字员工"

    def test_same_class_different_identity(self) -> None:
        """同一个类，不同 workspace → 不同身份（核心教学点）"""
        from shared.digital_worker import DigitalWorkerCrew
        mgr = DigitalWorkerCrew(workspace_dir=WORKSPACE_MANAGER, sandbox_port=8023)
        dev = DigitalWorkerCrew(workspace_dir=WORKSPACE_DEV, sandbox_port=8024)
        assert type(mgr) is type(dev)
        assert mgr.worker_agent().backstory != dev.worker_agent().backstory

    def test_sandbox_ports_isolated(self) -> None:
        from shared.digital_worker import DigitalWorkerCrew
        mgr = DigitalWorkerCrew(workspace_dir=WORKSPACE_MANAGER, sandbox_port=8023)
        dev = DigitalWorkerCrew(workspace_dir=WORKSPACE_DEV, sandbox_port=8024)
        assert mgr.sandbox_port != dev.sandbox_port

    def test_task_uses_universal_template(self) -> None:
        from shared.digital_worker import DigitalWorkerCrew, UNIVERSAL_TASK_TEMPLATE
        worker = DigitalWorkerCrew(workspace_dir=WORKSPACE_MANAGER, sandbox_port=8023)
        task = worker.worker_task()
        assert task.description == UNIVERSAL_TASK_TEMPLATE


# ── E2E 真实执行测试（需 Docker 沙盒 + LLM API）────────────────────────────
# 运行方式：pytest m4l25/test_m4l25.py -m e2e -v -s
# 前提：docker compose -f sandbox-docker-compose.yaml up -d

import subprocess
import socket


def _sandbox_reachable(port: int) -> bool:
    try:
        with socket.create_connection(("localhost", port), timeout=3):
            return True
    except OSError:
        return False


@pytest.mark.e2e
class TestTE2E1ManagerRealExecution:

    TIMEOUT = 300

    def test_sandbox_8023_reachable(self) -> None:
        assert _sandbox_reachable(8023), \
            "Manager 沙盒未启动，请先运行: docker compose -f sandbox-docker-compose.yaml up -d"

    def test_manager_produces_task_breakdown(self) -> None:
        output_path = WORKSPACE_MANAGER / "task_breakdown.md"
        if output_path.exists():
            output_path.unlink()

        result = subprocess.run(
            ["python3", "run_manager.py"],
            cwd=_M4L25_DIR,
            capture_output=False,
            timeout=self.TIMEOUT,
        )
        assert result.returncode == 0

    def _find_task_breakdown(self) -> Path | None:
        exact = WORKSPACE_MANAGER / "task_breakdown.md"
        if exact.exists():
            return exact
        candidates = sorted(WORKSPACE_MANAGER.glob("*task_breakdown*.md"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None

    def test_task_breakdown_exists(self) -> None:
        output_path = self._find_task_breakdown()
        assert output_path is not None

    def test_task_breakdown_has_roles(self) -> None:
        output_path = self._find_task_breakdown()
        if output_path is None:
            pytest.skip("task_breakdown 文件不存在")
        content = output_path.read_text(encoding="utf-8")
        assert "Dev" in content


@pytest.mark.e2e
class TestTE2E2DevRealExecution:

    TIMEOUT = 300

    def test_sandbox_8024_reachable(self) -> None:
        assert _sandbox_reachable(8024), \
            "Dev 沙盒未启动，请先运行: docker compose -f sandbox-docker-compose.yaml up -d"

    def test_dev_produces_tech_design(self) -> None:
        output_path = WORKSPACE_DEV / "tech_design.md"
        if output_path.exists():
            output_path.unlink()

        result = subprocess.run(
            ["python3", "run_dev.py"],
            cwd=_M4L25_DIR,
            capture_output=False,
            timeout=self.TIMEOUT,
        )
        assert result.returncode == 0

    def _find_tech_design(self) -> Path | None:
        exact = WORKSPACE_DEV / "tech_design.md"
        if exact.exists():
            return exact
        candidates = sorted(WORKSPACE_DEV.glob("*tech_design*.md"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None

    def test_tech_design_exists(self) -> None:
        output_path = self._find_tech_design()
        assert output_path is not None

    def test_tech_design_has_four_sections(self) -> None:
        output_path = self._find_tech_design()
        if output_path is None:
            pytest.skip("tech_design 文件不存在")
        content = output_path.read_text(encoding="utf-8")
        checks = [
            any(k in content for k in ["架构", "architecture", "Architecture"]),
            any(k in content for k in ["接口", "interface", "Interface", "API"]),
            any(k in content for k in ["实现", "implement", "Implement"]),
            any(k in content for k in ["测试", "test", "Test"]),
        ]
        assert sum(checks) >= 3