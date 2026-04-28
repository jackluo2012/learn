"""
共享工作区初始化工具 — 供单元测试和本地工具直接导入。

同一逻辑以 CLI 形式在 workspace/manager/skills/init_project/scripts/init_workspace.py 中实现，
供 Agent 在沙盒中通过 Bash 调用。
"""

from __future__ import annotations

from pathlib import Path


def create_workspace(
    shared_dir: Path,  # 共享工作区的根目录路径
    roles: list[str],  # 角色列表，用于创建对应的邮箱
    project_name: str = "",  # 可选的项目名称，用于生成工作区规则文档
) -> dict:  # 返回创建报告，包含创建的目录、文件和跳过的文件列表
    """创建共享工作区目录结构（幂等：已存在的文件不覆盖）。

    目录结构：
      shared_dir/
        needs/                  # 需求文档（Manager 写入）
        design/                 # 设计文档（PM 写入）
        mailboxes/              # 各角色邮箱
          {role}.json           # 初始空数组
        WORKSPACE_RULES.md      # 工作区访问规范

    返回创建报告：
      {
        "created_dirs":   [相对路径, ...],
        "created_files":  [相对路径, ...],
        "skipped_files":  [相对路径, ...],
      }
    """
    created_dirs: list[str]  = []  # 存储已创建的目录列表
    created_files: list[str] = []  # 存储已创建的文件列表
    skipped_files: list[str] = []  # 存储已存在而跳过的文件列表

    def _mkdir(path: Path, label: str) -> None:  # 内部函数：创建目录（如果不存在）
        if not path.exists():  # 检查目录是否存在
            path.mkdir(parents=True, exist_ok=True)  # 创建目录（包括父目录）
            created_dirs.append(label)  # 添加到已创建目录列表

    def _write_if_absent(path: Path, content: str, label: str) -> None:  # 内部函数：如果文件不存在则写入
        if path.exists():  # 检查文件是否存在
            skipped_files.append(label)  # 如果存在，添加到跳过列表
        else:
            path.write_text(content, encoding="utf-8")  # 写入文件内容
            created_files.append(label)  # 添加到已创建文件列表

    # 创建子目录
    _mkdir(shared_dir / "needs",    "needs/")      # 创建需求文档目录
    _mkdir(shared_dir / "design",   "design/")     # 创建设计文档目录
    _mkdir(shared_dir / "mailboxes","mailboxes/")  # 创建邮箱目录

    # 创建各角色邮箱（初始空数组）
    for role in roles:  # 遍历所有角色
        _write_if_absent(
            shared_dir / "mailboxes" / f"{role}.json",  # 邮箱文件路径
            "[]",  # 初始内容为空数组
            f"mailboxes/{role}.json",  # 文件标签
        )

    # 创建工作区访问规范
    rules_content = _build_workspace_rules(project_name, roles)  # 生成工作区规则内容
    _write_if_absent(
        shared_dir / "WORKSPACE_RULES.md",  # 规则文档路径
        rules_content,  # 规则内容
        "WORKSPACE_RULES.md",  # 文档标签
    )

    return {  # 返回创建结果报告
        "created_dirs":  created_dirs,   # 已创建的目录列表
        "created_files": created_files,  # 已创建的文件列表
        "skipped_files": skipped_files,  # 跳过的文件列表
    }


def _build_workspace_rules(project_name: str, roles: list[str]) -> str:
    project_line = f"# 共享工作区访问规范\n\n项目：{project_name or '（未命名）'}\n"
    return (
        f"{project_line}\n"
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