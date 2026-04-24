---
name: sop_manager
description: "Use this skill when you are a Manager agent and need to decompose a business requirement into a structured task list. Triggers: receiving a project requirement, feature request, or bug report that needs to be broken down into tasks with assigned roles and acceptance criteria. Do NOT use for writing code, modifying requirements, or executing tasks."
---

# Manager 任务拆解 SOP

## 概述

本 SOP 定义 Manager 接收需求后的标准拆解流程，确保每个任务可分配、可执行、可验收。

---

## 步骤 1：需求完整性检查

在拆解之前，确认以下字段均已明确：

| 检查项 | 说明 | 缺失时的处理 |
|--------|------|------------|
| 目标 | 这个需求要解决什么问题 | 向甲方确认 |
| 验收标准（DoD）| 做到什么程度算完成 | **必须澄清，不得假设** |
| 约束条件 | 时间、技术栈、资源限制 | 向甲方确认 |
| 优先级 | 哪些任务阻塞其他任务 | 按依赖关系推断 |

> ⚠️ 如果验收标准缺失，输出澄清问题清单，**不进行任务拆解**。

---

## 步骤 2：识别任务类型，选择分工模式

根据需求性质选择分工模式（三种基础模式）：

| 模式 | 适用场景 | 团队配置 |
|------|---------|---------|
| **流水线（Pipeline）** | 新功能开发，角色依赖顺序明确 | PM → Dev → QA |
| **协调者-工作者（Coordinator-Worker）** | 多个独立子任务，Manager 统一分配 | Manager → [Dev, QA 并行] |
| **并行扇出（Parallel Fan-out）** | 相同任务批量分配给多个执行者 | Manager → [Dev1, Dev2, ...] |

---

## 步骤 3：任务拆解

将需求拆解为最小可执行单元，每个任务满足：

```
任务 = 一个角色 + 一种输入 + 一种输出 + 可验收标准
```

**拆解检验清单**：
- [ ] 每个任务只有一个负责角色
- [ ] 任务间依赖关系明确（哪个任务必须先完成）
- [ ] 每个任务有独立的验收标准
- [ ] 任务数量适中（通常 3-7 个，超过 10 个考虑再分组）

---

## 步骤 4：输出 task_breakdown.md

使用标准格式输出任务清单：

```markdown
# 任务清单 - {项目名称}

## 项目概览
- 目标：...
- 分工模式：流水线 / 协调者-工作者 / 并行扇出
- 整体验收标准：...

## 任务列表

| 任务ID | 任务名称 | 负责角色 | 前置任务 | 输入 | 输出 | 验收标准 |
|--------|---------|---------|---------|------|------|---------|
| T-01   | ...     | PM      | —       | ...  | ...  | ...     |
| T-02   | ...     | Dev     | T-01    | ...  | ...  | ...     |

## 待确认事项
（如有需要人工确认的歧义，列在此处）
```

---

## 步骤 5：保存输出

调用 `memory-save` skill，将 task_breakdown.md 保存至 `/workspace/task_breakdown.md`。
