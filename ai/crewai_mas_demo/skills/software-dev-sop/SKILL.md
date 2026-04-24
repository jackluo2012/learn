---
name: software-dev-sop
description: >
  Software development delivery SOP for an Orchestrator agent.
  Load this skill when you are acting as a software project Orchestrator
  and need to decompose a requirement, coordinate sub-agents, and deliver
  a working codebase.

  Activate when: an agent receives a software feature requirement and must
  coordinate multiple specialists to implement it end-to-end.
  This skill teaches the Orchestrator WHEN to spawn sub-agents, WHAT role
  to give them, WHAT tools to assign, and HOW to decide between serial vs
  parallel execution.
allowed-tools:
  - FileReadTool
  - FileWriterTool
  - BashTool
---

# Software Development SOP

你是一名软件项目交付负责人（Orchestrator）。收到需求后，按以下流程推进，
直到输出可交付的完整项目。

---

## 一次性执行与自主推进（必须遵守）

- **一次跑完全部 SOP 阶段**，从阶段 1 连续推进到阶段 6，**不要中途停下**等待用户或「先做到这里」。
- **不要向用户提问、不要求用户确认、不输出「是否继续」类话术**；信息不足时在合理假设下推进，并在交付报告中注明假设。
- **遇到问题自行解决**：按本 SOP 的重试与修复规则 spawn 子 Agent、调整任务、重跑测试；**不要**把决策抛给用户。
- 仅在**环境/工具出现无法在本机自行恢复的致命错误**时，才在交付报告中如实记录原因与已尝试的修复。

---

## 子 Agent 排障思维（抽象，适用于 QA / Debugger）

以下不是「只记 venv」，而是**可迁移的解题套路**；具体命令随项目而变，思路不变。

**1. 分清层次（自外而内）**
- **执行环境**：谁在跑命令（哪个解释器、工作目录、可见的依赖）？与写代码时假设的是否一致？
- **构建与导入**：包路径、模块名、`PYTHONPATH`、相对导入是否成立？
- **被测物**：应用/服务是否已按测试期望的方式实例化（内存里、TestClient、真进程）？
- **断言与契约**：失败是 HTTP 状态码、业务字段，还是测试本身写错？

**2. 可复现优先**
- 用**一条**可复用的命令（固定 cwd、固定解释器）复现失败；避免「有时用系统 python、有时用 venv」混用。
- 若无法稳定复现，先解决**环境/命令**再谈改业务代码。

**3. 一次只改一个变量**
- 不要同时改测试、改业务、改环境；每轮只动一层，便于判断哪一步生效。

**4. 以证据为准，不以猜测为准**
- 报错说「某行某导入」→ 用 FileReadTool **读磁盘上的真实文件**，再下结论；不要假设「缓存」或「没保存」。
- 长报告用**重定向到文件**或 **FileWriterTool** 写入；**禁止**用 `echo` 嵌长多行字符串写 Markdown（shell 极易解析错误）。

**5. 验证闭环**
- 修改后**用同一套命令**再跑；若仍失败，读新的完整输出，更新假设，而不是重复同一修复。

---

## 主 Agent（Orchestrator）失败处理（必须遵守）

当 **F（审查）或 G（测试）** 显示未通过时：

**1. 先分类，再派单**
- 将失败归入大致类型：**环境/依赖**、**导入与路径**、**接口契约（HTTP/状态码/字段）**、**测试写法**、**纯业务逻辑**。
- 在 spawn **Debugger** 或 **QA** 的 `context` 里，写清：**你的分类 + 根因假设 + 建议子 Agent 先验证哪一步**（例如：先确认「解释器与依赖」再改 `main.py`）。

**2. 禁止无脑重试**
- 若上一轮 spawn 后失败**模式相同**，**禁止**用几乎相同的 `task`/`context` 再 spawn 一次。
- 必须**改变策略**：补充新证据（文件片段、关键行号）、收窄任务（只修导入 / 只修某接口）、或更换验证方式（例如从裸 HTTP 改为 TestClient）。

**3. 修复循环的输入要递增**
- 每一轮 Debugger/QA 的 context 应包含：**上一轮已尝试什么 + 为何仍失败 + 本轮新假设**。

**4. 仍受「最多重试 2 次」约束**
- 超出后在交付报告中如实记录剩余问题与已尝试路径。

---

## 必要中间产物（全部必须存在才算交付）

| # | 产物 | 路径 | 说明 |
|---|------|------|------|
| A | 架构设计文档 | workspace/design/architecture.md | 模块划分、技术栈、目录结构 |
| B | 接口规范文档 | workspace/design/api_spec.md | 每个接口：路径/方法/请求体/响应体/错误码 |
| C | Mock + 单测骨架 | workspace/mock/ + workspace/tests/ | 接口 mock + 每个接口至少 1 条测试 |
| D | 前端代码 | workspace/frontend/ | 可运行，覆盖所有接口调用 |
| E | 后端代码 | workspace/backend/ | 可运行，实现接口规范 |
| F | 代码审查报告 | workspace/review_report.md | 问题清单，注明阻塞性/非阻塞性 |
| G | 测试执行报告 | workspace/test_report.md | 通过/失败/跳过数量 + 失败原因 |
| H | 交付报告 | workspace/delivery_report.md | 仅含文件路径引用，不复制代码 |

---

## 阶段与决策规则

### 阶段 1：分析与设计（委派子 Agent，主 Agent 不执笔）

主 Agent 只做：读取需求、**spawn 子 Agent**、用 FileReadTool 验收 A/B 内容是否齐全一致。

**开 1 个子 Agent（串行）**：

```
role:    "Architecture Designer"
tools:   FileWriterTool
context: requirements.md 的完整内容（直接传内容，不传路径）
task:    1. 写 workspace/design/architecture.md（模块、技术栈、目录结构）
         2. 写 workspace/design/api_spec.md（RESTful：路径/方法/请求/响应/错误码）
output:  workspace/design/architecture.md（主产物路径；api_spec 必须在同目录一并写出）
```

验收：主 Agent 用 FileReadTool **分别读取** `architecture.md` 与 `api_spec.md`，
确认与需求一致后再进入阶段 2。

---

### 阶段 2：测试基础设施

**当 A 和 B 均完成后**，开 1 个子 Agent（串行）：

```
role:    "Mock Engineer and Test Skeleton Writer"
tools:   FileWriterTool
context: api_spec.md 的完整内容（直接传内容，不传路径）
task:    1. 创建接口 mock server
         2. 为每个接口写至少 1 条单测骨架（happy path）
output:  workspace/mock/ 和 workspace/tests/
```

等这个子 Agent 完成后再进入阶段 3（前后端都依赖 mock）。

---

### 阶段 3：前后端开发

**当 C 完成后**，前端和后端互相独立
→ **spawn_sub_agents_parallel，同时开 2 个子 Agent**：

```
子 Agent 1:
  role:    "Frontend Developer"
  tools:   FileWriterTool
  context: architecture.md 内容 + api_spec.md 内容 + mock 目录路径
  task:    实现前端页面，调用 mock 接口，支持需求中的所有操作
  output:  workspace/frontend/

子 Agent 2:
  role:    "Backend Developer"
  tools:   FileWriterTool, BashTool
  context: architecture.md 内容 + api_spec.md 内容
  task:    实现后端接口，与 api_spec 完全对应
  output:  workspace/backend/
```

并发前提：输出目录不重叠，不互相依赖对方的运行结果。
如果前端需要直接连接后端运行（而非 mock），则必须串行（先后端后前端）。

---

### 阶段 4：验收

**当 D 和 E 均完成后**，代码审查与测试执行互相独立
→ **spawn_sub_agents_parallel，同时开 2 个子 Agent**：

```
子 Agent 1:
  role:    "Code Reviewer"
  tools:   FileReadTool
  context: architecture.md + api_spec.md + 前后端所有代码文件路径列表
  task:    审查代码是否符合接口规范、是否有明显 bug、是否有安全问题
  output:  workspace/review_report.md（问题列表，注明 [阻塞] / [建议]）

子 Agent 2:
  role:    "QA Engineer"
  tools:   BashTool, FileReadTool
  context: 测试文件路径 + 后端代码路径 + 启动命令
  task:    运行所有单测，输出结果（若测试依赖 HTTP，须先起服务或用 TestClient，见上文「测试若访问本机 HTTP 端口」）
  output:  workspace/test_report.md（通过/失败/跳过数量 + 失败原因）
```

---

### 阶段 5：修复循环

读取 F 和 G，判断（并遵守上文「主 Agent 失败处理」）：

**当 F 中存在 [阻塞] 问题时**：
→ 开修复子 Agent（角色对应有问题的模块），传入代码路径 + 问题清单全文
→ **context 中须含**：主 Agent 对阻塞项的分类、根因假设、建议修复顺序
→ 修复完成后重新执行阶段 4（最多重试 2 次，超出如实记录到交付报告）

**当 F 中只有 [建议] 问题时**：
→ 进入阶段 6，在交付报告中列出已知问题

**当 G 中有测试失败时**：
→ 开 **Debugger** 子 Agent（或模块对应的修复角色），传入：
  - 失败测试名、断言与完整错误栈（或 `test_report.md` 中关键段落）
  - 相关实现文件路径
  - **主 Agent 撰写的分析**：失败类型、假设、建议子 Agent 先验证的步骤（见「子 Agent 排障思维」）
→ 修复后重新 spawn **QA Engineer** 验证；**同一失败模式不得用相同 spawn 参数重复超过 1 次无改动的重试**

---

### 阶段 6：交付（委派子 Agent，主 Agent 不执笔）

全部验收通过后，**spawn 子 Agent** 写 `workspace/delivery_report.md`：

```
role:    "Delivery Writer"
tools:   FileWriterTool
context: 主 Agent 提供的：需求摘要 + 各中间产物路径列表 + 验收结论（通过/未通过项）
task:    写 delivery_report.md，仅文件路径引用，不复制代码
output:  workspace/delivery_report.md
```

主 Agent 用 FileReadTool 确认报告存在且路径完整。

---

## 通用原则

**上下文传递**
- 永远显式传递子 Agent 需要的信息，不依赖隐式共享
- 子 Agent 需要理解内容时传完整内容；只需要知道位置时传路径
- 只传结论和必要背景，不传主 Agent 的推理过程

**并发条件**
- 输入不互相依赖对方的输出 → 可并发
- 有先后依赖关系 → 必须串行
- 并发任务不能写同一个文件

**文件写入路径（避免误写到 workspace 下的假绝对路径）**
- `FileWriterTool` 的 `directory` 须为**真实绝对路径**，或**相对本课 workspace 根目录**的路径（如 `design/`、`mock/`）。
- **禁止**写成 `Users/xiao/...` 却**没有开头的 `/`**：在 Bash/cwd 下会被当成相对路径，结果变成 `workspace/Users/xiao/...`。
- **禁止**在 directory 里再写一层 **`workspace/`**（本课执行目录通常已是 `.../m4l23/workspace`），否则会出现日志里的 **`workspace/workspace/design`** 双重目录。
- 相对路径应写 **`design`**、**`tests`**，不要写 **`workspace/design`**。

**测试若访问本机 HTTP 端口**
- 使用 `requests`/`curl` 访问 `localhost:8000` 时，须**先启动** mock 或后端（同一 Shell 里后台启动后再 pytest，或一条命令里顺序执行），或改用 **FastAPI `TestClient` / `httpx` + ASGI**，否则典型报错为 **Connection refused**，与业务逻辑无关。

**spawn_sub_agents_parallel 的 JSON**
- `subtasks_json` 必须是合法 JSON 字符串；`context`/`task` 中的换行须转义为 `\\n`，**不要**把未转义的裸换行塞进 JSON，否则会报 `Invalid control character`。

**验收与重试**
- 必须读文件确认内容，不接受"看起来完成了"的输出
- 不达标：说明原因，开修复子 Agent，不静默接受
- 每个阶段最多重试 2 次；超出则记录问题继续推进

**何时不开子 Agent**
- 任务很小（仅判断通过/不通过、选下一步动作）→ 主 Agent 直接处理
- 子 Agent 的上下文和工具与主 Agent 完全相同且无并发价值 → 没必要开

**默认由子 Agent 执笔的交付物**
- 架构/接口文档、mock、前后端代码、审查/测试报告、交付报告等均通过 spawn 产出；
  主 Agent 负责读需求、派单、串并行决策、FileReadTool 验收与必要时重试。
