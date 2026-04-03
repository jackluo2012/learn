"""
SkillLoaderTool 单元测试

测试覆盖：
  - DEFAULT_SANDBOX_MOUNT_DESC：常量存在且包含原 m2l16 挂载描述
  - build_skill_crew()：mount_desc 参数透传到 task description
  - SkillLoaderTool()：无参调用向下兼容（m2l16 行为不变）
  - SkillLoaderTool(sandbox_mount_desc=...)：自定义挂载描述被存储
  - _execute_skill_async()：task 型 Skill 时 mount_desc 传给 build_skill_crew

运行：
  cd crewai_mas_demo && pytest tools/test_skill_loader_tool.py -v
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_TOOLS_DIR = Path(__file__).parent
_PROJECT_ROOT = _TOOLS_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from tools.skill_loader_tool import (  # noqa: E402
    DEFAULT_SANDBOX_MOUNT_DESC,
    SkillLoaderTool,
    build_skill_crew,
)

_MODULE = "tools.skill_loader_tool"


# ─────────────────────────────────────────────────────────────────────────────
# 1. DEFAULT_SANDBOX_MOUNT_DESC 常量
# ─────────────────────────────────────────────────────────────────────────────

class TestDefaultSandboxMountDesc:

    def test_constant_exists_and_is_string(self):
        """DEFAULT_SANDBOX_MOUNT_DESC 存在且为字符串"""
        assert isinstance(DEFAULT_SANDBOX_MOUNT_DESC, str)
        assert len(DEFAULT_SANDBOX_MOUNT_DESC) > 0

    def test_contains_original_m2l16_data_mount(self):
        """常量包含 m2l16 原始的 data:ro 挂载描述"""
        assert "workspace/data" in DEFAULT_SANDBOX_MOUNT_DESC
        assert ":ro" in DEFAULT_SANDBOX_MOUNT_DESC

    def test_contains_original_m2l16_output_mount(self):
        """常量包含 m2l16 原始的 output:rw 挂载描述"""
        assert "workspace/output" in DEFAULT_SANDBOX_MOUNT_DESC
        assert ":rw" in DEFAULT_SANDBOX_MOUNT_DESC


# ─────────────────────────────────────────────────────────────────────────────
# 2. build_skill_crew() mount_desc 参数
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildSkillCrewMountDesc:

    @pytest.fixture(autouse=True)
    def patch_crew_deps(self):
        """屏蔽 Pydantic 校验严格的外部类，改验证调用参数"""
        with (
            patch(f"{_MODULE}.MCPServerHTTP"),
            patch(f"{_MODULE}.AliyunLLM"),
            patch(f"{_MODULE}.Agent") as mock_agent,
            patch(f"{_MODULE}.Task") as mock_task,
            patch(f"{_MODULE}.Crew"),
        ):
            self.mock_agent = mock_agent
            self.mock_task = mock_task
            yield

    def _get_task_description(self) -> str:
        """从 Task() 调用参数中提取 description"""
        assert self.mock_task.called, "Task() 未被调用"
        call_kwargs = self.mock_task.call_args
        return call_kwargs.kwargs.get("description") or call_kwargs.args[0]

    def test_default_mount_desc_used_when_no_arg(self):
        """不传 mount_desc 时，Task 的 description 包含默认 data:ro 挂载描述"""
        build_skill_crew("test-skill", "instructions")
        desc = self._get_task_description()
        assert "workspace/data" in desc

    def test_custom_mount_desc_applied(self):
        """传入自定义 mount_desc 时，Task 的 description 包含该描述"""
        custom = "自定义挂载：./workspace:/workspace:rw"
        build_skill_crew("test-skill", "instructions", mount_desc=custom)
        desc = self._get_task_description()
        assert "自定义挂载：./workspace:/workspace:rw" in desc

    def test_custom_mount_desc_replaces_default(self):
        """自定义 mount_desc 时，默认的 data:ro 描述不出现在 Task description 里"""
        custom = "仅自定义挂载"
        build_skill_crew("test-skill", "instructions", mount_desc=custom)
        desc = self._get_task_description()
        assert "workspace/data:/workspace/data:ro" not in desc

    def test_skill_instructions_in_agent_backstory(self):
        """skill_instructions 传入 Agent backstory（未因参数改动丢失）"""
        build_skill_crew("test-skill", "特定教学指令内容")
        assert self.mock_agent.called, "Agent() 未被调用"
        backstory = self.mock_agent.call_args.kwargs.get("backstory", "")
        assert "特定教学指令内容" in backstory


# ─────────────────────────────────────────────────────────────────────────────
# 3. SkillLoaderTool 向下兼容性
# ─────────────────────────────────────────────────────────────────────────────

class TestSkillLoaderToolBackwardCompatibility:

    @pytest.fixture(autouse=True)
    def patch_skills_dir(self, tmp_path):
        """用临时目录模拟 skills，避免依赖真实 crewai_mas_demo/skills/"""
        # 创建空的 load_skills.yaml，保证 _build_description 不崩溃
        (tmp_path / "load_skills.yaml").write_text("skills: []", encoding="utf-8")
        with patch(f"{_MODULE}.SKILLS_DIR", tmp_path):
            yield

    def test_no_args_instantiation_succeeds(self):
        """SkillLoaderTool() 无参调用不报错（m2l16 用法）"""
        tool = SkillLoaderTool()
        assert tool is not None

    def test_no_args_uses_default_mount_desc(self):
        """无参实例的 sandbox_mount_desc 等于 DEFAULT_SANDBOX_MOUNT_DESC"""
        tool = SkillLoaderTool()
        assert tool.sandbox_mount_desc == DEFAULT_SANDBOX_MOUNT_DESC

    def test_custom_mount_desc_stored(self):
        """传入自定义 mount_desc，实例存储自定义值"""
        custom = "./workspace:/workspace:rw\n../skills:/mnt/skills:rw"
        tool = SkillLoaderTool(sandbox_mount_desc=custom)
        assert tool.sandbox_mount_desc == custom

    def test_custom_mount_desc_differs_from_default(self):
        """自定义挂载描述与默认值不同"""
        custom = "./workspace:/workspace:rw"
        tool = SkillLoaderTool(sandbox_mount_desc=custom)
        assert tool.sandbox_mount_desc != DEFAULT_SANDBOX_MOUNT_DESC


# ─────────────────────────────────────────────────────────────────────────────
# 4. _execute_skill_async：mount_desc 传递
# ─────────────────────────────────────────────────────────────────────────────

class TestExecuteSkillAsyncMountDesc:

    @pytest.fixture
    def tool_with_custom_mount(self, tmp_path):
        """创建使用自定义挂载的 SkillLoaderTool，注册一个假的 task 型 Skill"""
        custom_mount = "自定义挂载描述"
        (tmp_path / "load_skills.yaml").write_text(
            "skills:\n  - name: fake-skill\n    type: task\n    enabled: true",
            encoding="utf-8",
        )
        (tmp_path / "fake-skill").mkdir()
        (tmp_path / "fake-skill" / "SKILL.md").write_text(
            "---\nname: fake-skill\ndescription: test\n---\n正文",
            encoding="utf-8",
        )
        with patch(f"{_MODULE}.SKILLS_DIR", tmp_path):
            tool = SkillLoaderTool(sandbox_mount_desc=custom_mount)
        return tool, custom_mount

    @pytest.mark.asyncio
    async def test_task_skill_passes_mount_desc_to_build_skill_crew(
        self, tool_with_custom_mount
    ):
        """task 型 Skill 执行时，build_skill_crew 被以 sandbox_mount_desc 调用"""
        tool, custom_mount = tool_with_custom_mount

        mock_crew = MagicMock()
        mock_crew.akickoff = AsyncMock(return_value="ok")

        with patch(f"{_MODULE}.build_skill_crew", return_value=mock_crew) as mock_build:
            await tool._execute_skill_async("fake-skill", "任务描述")

        # 验证 build_skill_crew 被调用时传入了 mount_desc=自定义挂载描述
        call_kwargs = mock_build.call_args
        assert call_kwargs is not None
        # 支持位置参数或关键字参数两种写法
        passed_mount = (
            call_kwargs.kwargs.get("mount_desc")
            or (call_kwargs.args[2] if len(call_kwargs.args) > 2 else None)
        )
        assert passed_mount == custom_mount