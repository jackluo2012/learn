"""T6-T8 + T_extra3: HookLoader 单元测试。"""

import textwrap
from pathlib import Path

from hook_framework.registry import EventType, HookContext, HookRegistry
from hook_framework.loader import HookLoader


def _write_hook_dir(tmp_path: Path, yaml_content: str, handler_code: str, module_name: str = "my_handler"):
    hooks_dir = tmp_path / "hooks_dir"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.yaml").write_text(yaml_content)
    (hooks_dir / f"{module_name}.py").write_text(handler_code)
    return hooks_dir


# T6: 加载 yaml + handler
def test_load_from_directory(tmp_path):
    yaml_content = textwrap.dedent("""\
        hooks:
          BEFORE_TURN:
            - handler: my_handler.on_turn
    """)
    handler_code = textwrap.dedent("""\
        calls = []
        def on_turn(ctx):
            calls.append(ctx)
    """)
    hooks_dir = _write_hook_dir(tmp_path, yaml_content, handler_code)

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_from_directory(hooks_dir, layer_name="test")
    assert registry.handler_count(EventType.BEFORE_TURN) == 1


# T7: 两层合并
def test_two_layer_merge(tmp_path):
    global_dir = tmp_path / "global"
    global_dir.mkdir()
    (global_dir / "hooks.yaml").write_text(textwrap.dedent("""\
        hooks:
          TASK_COMPLETE:
            - handler: g_handler.on_complete
    """))
    (global_dir / "g_handler.py").write_text("def on_complete(ctx): pass")

    ws_dir = tmp_path / "workspace"
    ws_hooks = ws_dir / "hooks"
    ws_hooks.mkdir(parents=True)
    (ws_hooks / "hooks.yaml").write_text(textwrap.dedent("""\
        hooks:
          TASK_COMPLETE:
            - handler: w_handler.on_complete
    """))
    (ws_hooks / "w_handler.py").write_text("def on_complete(ctx): pass")

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_two_layers(global_dir, ws_dir)
    assert registry.handler_count(EventType.TASK_COMPLETE) == 2


# T8: 缺 yaml 不报错
def test_missing_yaml(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_from_directory(empty_dir)
    assert registry.handler_count(EventType.BEFORE_TURN) == 0


# T_extra3: yaml 引用不存在的模块
def test_missing_module_skipped(tmp_path):
    hooks_dir = tmp_path / "hooks_dir"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.yaml").write_text(textwrap.dedent("""\
        hooks:
          BEFORE_TURN:
            - handler: nonexistent_module.do_stuff
    """))

    registry = HookRegistry()
    loader = HookLoader(registry)
    loader.load_from_directory(hooks_dir, layer_name="test")
    assert registry.handler_count(EventType.BEFORE_TURN) == 0