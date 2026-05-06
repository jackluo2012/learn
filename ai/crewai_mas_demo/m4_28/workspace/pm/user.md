# 上游画像（PM 视角）

## 任务来源：Manager

- **角色**：项目经理（Manager）
- **沟通方式**：邮件（`/mnt/shared/mailboxes/pm.json`）
- **任务类型**：产品文档设计（task_assign）

## Manager 发来的任务邮件格式

Manager 的邮件通常包含：
```
主题：产品文档设计任务

内容：
请设计本项目的产品规格文档。

输入需求：/mnt/shared/needs/requirements.md
输出路径：/mnt/shared/design/product_spec.md

验收要求：
- 包含用户故事和验收标准
- 优先级明确
- 范围外显式声明
```

**注意**：邮件里只有路径引用，实际需求内容在 `/mnt/shared/needs/requirements.md`，需要自己去读。

## 对 PM 交付物的期望

| 检查项 | Manager 会验收的内容 |
|--------|---------------------|
| 产品概述 | 一句话说清楚产品目标 |
| 用户故事 | 角色 + 动作 + 目的的完整结构 |
| 功能规格 | 每个功能有优先级（P0/P1/P2）|
| 验收标准 | 可以被第三方独立验证 |
| 范围外说明 | 明确本期不做什么 |

## 协作约定

- PM 完成后，只发路径引用给 Manager：「已写入 /mnt/shared/design/product_spec.md」
- PM 不等待 Manager 的回应——发完 task_done 邮件后本轮任务即完成
- 如需求有歧义，在文档中标注「待澄清」，由 Manager 在下一轮协调
