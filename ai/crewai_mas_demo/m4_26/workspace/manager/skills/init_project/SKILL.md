---
name: init_project
type: task
description: 初始化共享工作区，创建 needs/、design/、mailboxes/ 目录和邮箱文件。新项目启动时由 Manager 调用。
---

# 初始化项目工作区

⚠️ 重要：通过 `skill_loader` 加载本 Skill 后，在沙盒中执行以下命令。

初始化脚本位置（沙盒内）：`/workspace/skills/init_project/scripts/init_workspace.py`

## 安装依赖

```bash
# 无额外依赖，使用标准库
```

## 初始化共享工作区

```bash
python3 /workspace/skills/init_project/scripts/init_workspace.py \
    --shared-dir /mnt/shared \
    --roles manager pm \
    --project-name "JackClaw 宠物健康记录"
```

## 将需求文档写入工作区

初始化后，将项目需求写入 `/mnt/shared/needs/requirements.md`：

```bash
cat > /mnt/shared/needs/requirements.md << 'EOF'
（需求内容）
EOF
```

## 命令输出（JSON 格式）

```json
{
  "errcode": 0,
  "data": {
    "created_dirs":  ["needs/", "design/", "mailboxes/"],
    "created_files": ["mailboxes/manager.json", "mailboxes/pm.json", "WORKSPACE_RULES.md"],
    "skipped_files": []
  }
}
```

## 幂等说明

- 重复调用安全：已存在的目录和文件不会被覆盖
- 已有邮件的 .json 文件不会被清空
