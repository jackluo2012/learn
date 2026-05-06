---
name: init_project
type: task
description: 初始化共享工作区，第27课新增 sop/ 目录和 human.json 邮箱。新项目启动时由 Manager 调用。
---

# 初始化项目工作区（第27课·含 Human 角色）

⚠️ 重要：通过 `skill_loader` 加载本 Skill 后，在沙盒中执行以下命令。

初始化脚本位置（沙盒内）：`/workspace/skills/init_project/scripts/init_workspace.py`

## 安装依赖

```bash
# 无额外依赖，使用标准库
```

## 初始化共享工作区（第27课：roles 必须包含 human）

```bash
python3 /workspace/skills/init_project/scripts/init_workspace.py \
    --shared-dir /mnt/shared \
    --roles manager pm human \
    --project-name "宠物健康记录App"
```

## 命令输出（JSON 格式）

```json
{
  "errcode": 0,
  "data": {
    "created_dirs":  ["needs/", "design/", "mailboxes/", "sop/"],
    "created_files": ["mailboxes/manager.json", "mailboxes/pm.json", "mailboxes/human.json", "WORKSPACE_RULES.md"],
    "skipped_files": []
  }
}
```

## 第27课新增目录

| 目录 | 用途 |
|------|------|
| `sop/` | SOP 模板库（product_design_sop.md 等） |

## 第27课新增邮箱

| 文件 | Schema | 操作方式 |
|------|--------|---------|
| `mailboxes/human.json` | 二态（`read: false/true`） | 由 `human_cli.py` 读写 |

## 幂等说明

- 重复调用安全：已存在的目录和文件不会被覆盖
- 已有邮件的 .json 文件不会被清空
