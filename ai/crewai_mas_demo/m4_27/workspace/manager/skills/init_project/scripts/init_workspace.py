#!/usr/bin/env python3
"""
初始化项目共享工作区 CLI — Agent 通过 Bash 在沙盒中调用。

第27课新增（相比第26课）：
  - 新增 sop/ 目录（SOP 模板库）
  - 支持 human.json 邮箱（二态 Schema，初始为空数组）
  - roles 参数应包含 human：--roles manager pm human

沙盒内调用示例：
  python3 /workspace/skills/init_project/scripts/init_workspace.py \\
      --shared-dir /mnt/shared \\
      --roles manager pm human \\
      --project-name "宠物健康记录App"
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

    # 第26课共有目录
    _mkdir(shared_dir / "needs",     "needs/")
    _mkdir(shared_dir / "design",    "design/")
    _mkdir(shared_dir / "mailboxes", "mailboxes/")
    # 第27课新增
    _mkdir(shared_dir / "sop",       "sop/")

    # 默认 SOP 模板（避免空库导致 sop_selector 报错）
    default_sop = shared_dir / "sop" / "product_design_sop.md"
    _write_if_absent(
        default_sop,
        "# 产品设计标准操作流程（SOP）\n"
        "\n"
        "## 角色分工\n"
        "| 角色 | 职责 |\n"
        "|------|------|\n"
        "| Manager | 需求分析、SOP 选择、任务分配、进度跟踪 |\n"
        "| PM | 产品文档设计、用户故事编写、验收标准制定 |\n"
        "| Human | 需求确认、SOP 确认、里程碑验收 |\n"
        "\n"
        "## 执行步骤\n"
        "| 步骤 | 执行者 | 操作 | 输入 | 输出 |\n"
        "|------|--------|------|------|------|\n"
        "| 1 | Manager | 需求分析，提取关键特征 | 用户需求描述 | 结构化需求文档 |\n"
        "| 2 | Manager | 选择匹配 SOP 模板 | 需求文档 | active_sop.md |\n"
        "| 3 | PM | 编写产品文档（用户故事+验收标准） | 需求文档 + SOP | 产品文档 |\n"
        "| 4 | Human | 验收产品文档 | 产品文档 | 验收结果 |\n"
        "\n"
        "## 检查点（Human 确认节点）\n"
        "| 检查点 | 触发时机 | 确认内容 |\n"
        "|--------|---------|---------|\n"
        "| CP1 | 需求文档完成后 | 需求是否准确完整，是否符合预期 |\n"
        "| CP2 | 产品文档完成后 | 用户故事是否清晰，验收标准是否可验证 |\n"
        "\n"
        "## 质量标准\n"
        "| 交付物 | 验收标准 |\n"
        "|--------|---------|\n"
        "| 需求文档 | 包含目标、边界、约束、风险四维度 |\n"
        "| 产品文档 | 每个用户故事有明确的验收标准，PM 自评通过 |\n"
        "| 最终产品 | Human 验收通过（human.json 中 read: true） |\n",
        "sop/product_design_sop.md",
    )

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
        "| `/mnt/shared/needs/` | Manager 写，所有人读 | 需求文档 |\n"
        "| `/mnt/shared/design/` | PM 写，Manager 读 | 产品文档 |\n"
        "| `/mnt/shared/mailboxes/` | 通过 mailbox Skill 操作 | 角色间通信 |\n"
        "| `/mnt/shared/sop/` | Manager 写，PM 读 | SOP 模板库 |\n\n"
        "## 邮箱规范\n\n"
        "- **Agent 邮箱**（manager/pm）：三态状态机（unread → in_progress → done）\n"
        "- **Human 邮箱**（human）：二态（read: false → true），由 human_cli.py 操作\n"
        "- 单一接口约束：只有 Manager 可以向 human.json 发消息\n"
        "- 邮件内容只写路径引用，不把文档全文放进邮件\n"
    )
    _write_if_absent(shared_dir / "WORKSPACE_RULES.md", rules, "WORKSPACE_RULES.md")

    return {
        "created_dirs":  created_dirs,
        "created_files": created_files,
        "skipped_files": skipped_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化项目共享工作区（第27课·含 human.json + sop/）")
    parser.add_argument("--shared-dir", required=True, help="共享工作区路径（沙盒内）")
    parser.add_argument("--roles", nargs="+", default=["manager", "pm", "human"],
                        help="角色列表（第27课建议：manager pm human）")
    parser.add_argument("--project-name", default="", help="项目名称（写入 WORKSPACE_RULES.md）")
    args = parser.parse_args()

    shared_dir = Path(args.shared_dir)
    result = create_workspace(shared_dir, args.roles, args.project_name)

    print(json.dumps({"errcode": 0, "data": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
