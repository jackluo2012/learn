#!/usr/bin/env python3
"""
初始化项目共享工作区 CLI — Agent 通过 Bash 在沙盒中调用。

功能：
  - 创建 needs/、design/、mailboxes/ 子目录
  - 为每个角色创建初始邮箱文件（空 JSON 数组）
  - 生成 WORKSPACE_RULES.md（幂等：已存在的文件不覆盖）

沙盒内调用示例：
  python3 /workspace/skills/init_project/scripts/init_workspace.py \\
      --shared-dir /mnt/shared \\
      --roles manager pm \\
      --project-name "JackClaw 宠物健康记录"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def create_workspace(
    shared_dir: Path,
    roles: list[str],
    project_name: str = "",
) -> dict:
    """创建共享工作区目录结构（幂等）。"""
    created_dirs: list[str]  = []
    created_files: list[str] = []
    skipped_files: list[str] = []

    def _mkdir(path: Path, label: str) -> None:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(label)

    def _write_if_absent(path: Path, content: str, label: str) -> None:
        if path.exists():
            skipped_files.append(label)
        else:
            path.write_text(content, encoding="utf-8")
            created_files.append(label)

    _mkdir(shared_dir / "needs",     "needs/")
    _mkdir(shared_dir / "design",    "design/")
    _mkdir(shared_dir / "mailboxes", "mailboxes/")

    for role in roles:
        _write_if_absent(
            shared_dir / "mailboxes" / f"{role}.json",
            "[]",
            f"mailboxes/{role}.json",
        )

    rules = (
        f"# 共享工作区访问规范\n\n项目：{project_name or '（未命名）'}\n\n"
        "## 目录权限\n\n"
        "| 目录 | 权限 | 说明 |\n"
        "|------|------|------|\n"
        "| `/mnt/shared/needs/` | 只读（所有角色）| 需求文档来源，不得修改 |\n"
        "| `/mnt/shared/design/` | 可读写（PM）| PM 输出产品文档 |\n"
        "| `/mnt/shared/mailboxes/` | 可读写（通过 mailbox skill）| 角色间通信 |\n\n"
        "## 邮箱规范\n\n"
        "- 邮件内容只写路径引用，不把文档全文放进邮件\n"
        "- 消息类型：`task_assign`（任务分配）/ `task_done`（任务完成）\n"
        "- 消息状态：`unread` → `in_progress` → `done`（三态状态机）\n"
    )
    _write_if_absent(shared_dir / "WORKSPACE_RULES.md", rules, "WORKSPACE_RULES.md")

    return {
        "created_dirs":  created_dirs,
        "created_files": created_files,
        "skipped_files": skipped_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化项目共享工作区")
    parser.add_argument("--shared-dir", required=True, help="共享工作区路径（沙盒内）")
    parser.add_argument("--roles", nargs="+", default=["manager", "pm"],
                        help="角色列表，用于创建对应邮箱文件")
    parser.add_argument("--project-name", default="", help="项目名称（写入 WORKSPACE_RULES.md）")
    args = parser.parse_args()

    shared_dir = Path(args.shared_dir)
    result = create_workspace(shared_dir, args.roles, args.project_name)

    print(json.dumps({"errcode": 0, "data": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
