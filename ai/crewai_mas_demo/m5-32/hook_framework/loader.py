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
        self._strategies: dict[str, object] = {}  # 存储加载策略
        self._module_cache: dict[str, object] = {}  # 模块缓存字典，用于存储已加载的模块

    def _load_module(self, hooks_dir: Path, module_name: str, layer_name: str):
        module_path = (hooks_dir / f"{module_name}.py").resolve()
        if not module_path.is_relative_to(hooks_dir.resolve()):
            raise FileNotFoundError(
                f"path traversal blocked: {module_name}"
            )
        if not module_path.exists():
            raise FileNotFoundError(
                f"module not found: {module_path}"
            )
        fq_name = f"hooks.{layer_name}.{module_name}"
        if fq_name in self._module_cache:
            return self._module_cache[fq_name]
        spec = importlib.util.spec_from_file_location(fq_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._module_cache[fq_name] = module
        return module

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
        
        # strategies 段：有状态类实例化（31课新增）
        # 顺序敏感：列表顺序 = 注册顺序 = 执行顺序
        for entry in config.get("strategies", []):
            class_ref = entry.get("class", "")
            if not class_ref or "." not in class_ref:
                print(
                    f"[HookLoader] invalid strategy class: {class_ref}",
                    file=sys.stderr,
                )
                continue

            module_name, class_name = class_ref.rsplit(".", 1)
            try:
                module = self._load_module(hooks_dir, module_name, layer_name)
            except FileNotFoundError as e:
                print(f"[HookLoader] strategy {class_ref}: {e}", file=sys.stderr)
                continue

            cls = getattr(module, class_name, None)
            if cls is None:
                print(
                    f"[HookLoader] class not found: {class_ref}",
                    file=sys.stderr,
                )
                continue
            

            resolved_deps = {}
            for param, ref_key in entry.get("deps", {}).items():
                if ref_key not in self._strategies:
                    print(
                        f"[HookLoader] dep '{ref_key}' not found for "
                        f"{class_ref}.{param} — declare it earlier in strategies",
                        file=sys.stderr,
                    )
                    continue
                resolved_deps[param] = self._strategies[ref_key]

            try:
                instance = cls(**entry.get("config", {}), **resolved_deps)
            except TypeError as e:
                print(
                    f"[HookLoader] failed to instantiate {class_ref}: {e}",
                    file=sys.stderr,
                )
                continue

            for event_name, method_name in entry.get("hooks", {}).items():
                event_type = EventType(event_name.lower())
                handler = getattr(instance, method_name, None)
                if handler is None:
                    print(
                        f"[HookLoader] method not found: {class_ref}.{method_name}",
                        file=sys.stderr,
                    )
                    continue
                display = f"[{layer_name}] {class_ref}.{method_name}"
                self._registry.register(event_type, handler, name=display)

            strategy_key = module_name
            self._strategies[strategy_key] = instance



    def load_two_layers(self, global_dir: Path, workspace_dir: Path):
        self.load_from_directory(global_dir, layer_name="global")
        ws_hooks = workspace_dir / "hooks"
        if ws_hooks.exists():
            self.load_from_directory(ws_hooks, layer_name="workspace")

    @property
    def strategies(self) -> dict[str, object]:

        """获取当前策略字典的副本
        
        Returns:
            dict[str, object]: 包含策略的字典，键为策略名称，值为策略对象
        """
        return dict(self._strategies)              # 返回策略字典的副本，防止外部直接修改内部状态