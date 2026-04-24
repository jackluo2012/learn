---
name: workspace-rules
description: 共享工作区访问规范（第26课·reference skill）。注入 Agent 上下文，告知每个角色在 /mnt/shared/ 中的读写权限边界。
type: reference
---

# 共享工作区访问规范

## 目录结构

```
/mnt/shared/
├── WORKSPACE_RULES.md      # 本规范（只读）
├── mailboxes/              # 邮箱目录
│   ├── manager.json        # Manager 邮箱
│   └── pm.json             # PM 邮箱
├── needs/                  # 需求目录（Manager写，其他角色只读）
│   └── requirements.md
└── design/                 # 产品设计目录（PM写，其他角色只读）
    └── product_spec.md
```

## 权限表

| 角色 | needs/ | design/ | mailboxes/ |
|------|--------|---------|-----------|
| Manager | 读写 | 只读 | 通过 mailbox-ops 操作 |
| PM | **只读** | **读写** | 通过 mailbox-ops 操作 |

## 关键规则

1. **邮箱只通过 mailbox-ops skill 操作**，不直接读写 JSON 文件
2. **邮件内容只传路径引用**，不传文档全文
3. **PM 不得写入 needs/**，需求由 Manager 维护
4. **Manager 不得写入 design/**，产品设计由 PM 维护
