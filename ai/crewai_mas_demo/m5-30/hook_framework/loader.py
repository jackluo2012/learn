"""F3-F4: hooks.yaml 解析 + 两层自动加载。"""

import importlib.util
import sys
from pathlib import Path

import yaml

from .registry import EventType, HookRegistry


class HookLoader:
    def __init__(self, registry: HookRegistry):

        """
        初始化HookLoader实例
        
        参数:
            registry: HookRegistry实例，用于注册和管理钩子处理器
        """
        self._registry = registry  # 存储钩子注册表
        self._module_cache: dict[str, object] = {}  # 模块缓存字典，用于存储已加载的模块

    def load_from_directory(self, hooks_dir: Path, layer_name: str = ""):
        yaml_path = hooks_dir / "hooks.yaml"
        if not yaml_path.exists():
            return
        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        for event_name, handler_list in config.get("hooks", {}).items():
            event_type = EventType(event_name.lower())
            for entry in handler_list:
                handler_ref = entry["handler"]
                module_name, func_name = handler_ref.rsplit(".", 1)
                module_path = (hooks_dir / f"{module_name}.py").resolve()
                if not module_path.is_relative_to(hooks_dir.resolve()):
                    print(
                        f"[HookLoader] path traversal blocked: {handler_ref}",
                        file=sys.stderr,
                    )
                    continue
                if not module_path.exists():
                    print(
                        f"[HookLoader] module not found: {module_path}",
                        file=sys.stderr,
                    )
                    continue
                fq_name = f"hooks.{layer_name}.{module_name}"
                if fq_name in self._module_cache:
                    module = self._module_cache[fq_name]
                else:
                    spec = importlib.util.spec_from_file_location(fq_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._module_cache[fq_name] = module
                handler_fn = getattr(module, func_name, None)
                if handler_fn is None:
                    print(
                        f"[HookLoader] function not found: {handler_ref}",
                        file=sys.stderr,
                    )
                    continue
                display = f"[{layer_name}] {handler_ref}"
                self._registry.register(event_type, handler_fn, name=display)

    def load_two_layers(self, global_dir: Path, workspace_dir: Path):
        self.load_from_directory(global_dir, layer_name="global")
        ws_hooks = workspace_dir / "hooks"
        if ws_hooks.exists():
            self.load_from_directory(ws_hooks, layer_name="workspace")