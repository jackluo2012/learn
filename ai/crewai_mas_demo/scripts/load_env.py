#!/usr/bin/env python3
"""
加载 .env 环境变量到当前进程

用法（Python 脚本开头调用一次）：
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts import load_env
    load_env.setup()

    import os
    print(os.getenv("QWEN_API_KEY"))   # 直接可用

用法（Shell 中加载后再运行脚本）：
    source <(python scripts/load_env.py --export)
    python your_script.py

用法（直接运行，查看所有变量名）：
    python scripts/load_env.py --show
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _get_dotenv():
    """优先从 .venv 导入 dotenv（项目标准环境），fallback 到系统 python-dotenv"""
    try:
        # 先尝试 .venv
        venv_dotenv = _PROJECT_ROOT / ".venv" / "lib"
        for p in venv_dotenv.iterdir():
            if p.is_dir() and (p / "site-packages" / "dotenv").exists():
                sys.path.insert(0, str(p / "site-packages"))
                break
        from dotenv import load_dotenv as _load
        return _load
    except ImportError:
        pass

    # fallback 系统 python-dotenv
    from dotenv import load_dotenv as _load
    return _load


def setup(env_path: str | Path | None = None, verbose: bool = False) -> None:
    """
    将 .env 加载到 os.environ（覆盖同名变量）。

    Args:
        env_path: .env 文件路径，默认取项目根目录/.env
        verbose:  True 时打印每个变量名（前 4 字符 + ***）
    """
    path = Path(env_path) if env_path else _PROJECT_ROOT / ".env"

    _load = _get_dotenv()
    _load(path, override=True)

    if verbose:
        # 打印但不暴露真实内容
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                val = line.split("=", 1)[1].strip().strip("'\"")

                display = val[:4] + "***" if len(val) > 4 else "***"
                print(f"  {key} = {display}")

    print(f"[load_env] Done. ({path})")


def export_shell(env_path: str | Path | None = None) -> str:
    """
    生成 shell export 命令，用于 source <(python load_env.py --export)

    Returns:
        str: 每行 "export KEY='VALUE'" 格式
    """
    path = Path(env_path) if env_path else _PROJECT_ROOT / ".env"
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, raw_val = line.partition("=")
            key = key.strip()
            value = raw_val.strip().strip("'\"").replace("'", "'\\''")
            lines.append(f"export {key}='{value}'")
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="加载 .env 到当前进程")
    parser.add_argument("--env", "-e", default=None,
                        help=".env 文件路径（默认: 项目根目录/.env）")
    parser.add_argument("--export", action="store_true",
                        help="输出 shell export 命令（用于 source <(python load_env.py --export)）")
    parser.add_argument("--show", action="store_true",
                        help="打印所有变量名")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细模式：打印每个变量名（前 4 字符 + ***）")
    args = parser.parse_args()

    if args.export:
        print(export_shell(args.env))
        return

    setup(args.env, verbose=args.verbose)

    if args.show:
        path = Path(args.env) if args.env else _PROJECT_ROOT / ".env"
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                print(key)


if __name__ == "__main__":
    main()
