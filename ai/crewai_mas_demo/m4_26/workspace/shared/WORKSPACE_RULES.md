# 共享工作区访问规范

项目：JackClaw 宠物健康记录

## 目录权限

| 目录 | 权限 | 说明 |
|------|------|------|
| `/mnt/shared/needs/` | 只读（所有角色）| 需求文档来源，不得修改 |
| `/mnt/shared/design/` | 可读写（PM）| PM 输出产品文档 |
| `/mnt/shared/mailboxes/` | 可读写（通过 mailbox skill）| 角色间通信 |

## 邮箱规范

- 邮件内容只写路径引用，不把文档全文放进邮件
- 消息类型：`task_assign`（任务分配）/ `task_done`（任务完成）
- 消息状态：`unread` → `in_progress` → `done`（三态状态机）
