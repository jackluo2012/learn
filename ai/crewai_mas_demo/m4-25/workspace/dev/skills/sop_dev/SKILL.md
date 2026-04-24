---
name: sop_dev
description: "Use this skill when you are a Dev agent and need to produce a technical design document for a feature. Triggers: receiving a feature requirement or task assignment with clear acceptance criteria. Do NOT use for writing requirement documents, doing integration/E2E testing, or modifying task assignments."
---

# Dev 技术设计 SOP

## 概述

本 SOP 定义 Dev 接收任务单后的标准技术设计流程，确保每个功能有可实现、可测试的技术方案。

---

## 步骤 1：任务单完整性检查

在开始设计之前，确认以下字段均已明确：

| 检查项 | 说明 | 缺失时的处理 |
|--------|------|------------|
| 功能描述 | 要实现什么功能 | 向 Manager 提出澄清请求 |
| 输入/输出格式 | 接口的输入和输出数据结构 | 向 Manager 提出澄清请求 |
| 验收标准（DoD）| 做到什么程度算完成 | **必须有，没有则退回 Manager** |
| 技术约束 | 语言、框架、性能要求 | 按团队约定推断，有疑义时确认 |

> ⚠️ 验收标准缺失时，输出澄清请求，**不进行技术设计**。

---

## 步骤 2：架构分析

分析功能在系统中的定位：

- **模块归属**：这个功能属于哪个模块，依赖哪些已有模块
- **复杂度评估**：简单工具函数 / 独立模块 / 需要新增服务
- **关键风险**：外部依赖（API/数据库）、并发、错误处理

---

## 步骤 3：接口设计

定义清晰的接口边界（选择适用的格式）：

**函数接口**：
```python
def parse_schedule(text: str, base_date: datetime) -> dict[str, Any]:
    """
    解析自然语言日程描述。

    Args:
        text: 用户输入的中文日程描述
        base_date: 相对时间的基准日期

    Returns:
        {
            "title": str,
            "start_time": str,  # ISO 8601 格式
            "end_time": str,
            "location": str,
            "attendees": list[str]
        }

    Raises:
        ParseError: 输入无法解析为有效日程
    """
```

---

## 步骤 4：实现要点

列出核心逻辑的关键决策点（不是完整代码，是实现路线图）：

- 技术方案选型及理由
- 核心算法或处理流程（可用伪代码）
- 错误处理策略
- 性能优化考量（如需）

---

## 步骤 5：单元测试用例

覆盖：正常路径（2-3个）+ 边界用例（2-3个）+ 异常路径（1-2个）

```markdown
| 用例ID | 用例名称 | 输入 | 期望输出 | 类型 |
|--------|---------|------|---------|------|
| UT-01  | 标准日程解析 | "明天下午3点开会" | {start: "2026-...", ...} | 正常 |
| UT-02  | 时间范围解析 | "2点到4点代码评审" | {start: ..., end: ...} | 正常 |
| UT-03  | 相对时间-下周 | "下周一上午10点" | ... | 边界 |
| UT-04  | 无效输入 | "随便说点什么" | ParseError | 异常 |
```

---

## 步骤 6：输出 tech_design.md

使用标准四段格式输出，保存至 `/workspace/tech_design.md`：

```markdown
# 技术设计 - {功能名称}

## 1. 架构说明

## 2. 接口定义

## 3. 实现要点

## 4. 单元测试用例
```

---

## 步骤 7：保存输出

调用 `skill_loader` 工具，保存 tech_design.md：

```
skill_name: "memory-save"
task_context: |
  将以下内容保存到 /workspace/tech_design.md（覆盖写入）：
  {完整的 tech_design.md 内容}

  预期输出 JSON schema：
  {
    "errcode": 0（成功）或非0（失败）,
    "errmsg": "success" 或错误信息,
    "path": "/workspace/tech_design.md",
    "bytes_written": 写入字节数
  }
```

> ⚠️ 注意：必须调用 `skill_loader` 工具（不是直接调用 `memory-save`）。`skill_loader` 是你唯一的工具入口。
