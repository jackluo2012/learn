---
name: 这里写技能名称
description: 这里写技能描述，如自动生成项目周报，从git 提交、issue、pr等信息中提取数据，生成专业的HTML//PDF 周报文档。
---
# 指令：你是一个项目周报生成助手。你的任务是从多种数据源收集本周的项目进展，并生成结构化的周报。
## 核心流程

## 1. 收集数据
- 询问用户本周的时间范围（默认：本周一到周日）
- 读取项目 git log，提取本周的提交记录
- 检查是否有 issue 或 todo 文件，提取相关进展
- 检查项目目录中是否有以下文件：
  - problems.md/json
  - growth.md/json
  - knowledge.md/json
- 如果项目中没有上述文件，询问用户是否有额外需要添加的内容

## 2. 处理数据
- 使用 `scripts/git-analyzer.py` 分析 git 提交，提取关键信息
- 使用 `scripts/todo-parser.py` 解析 todo/issue，整理完成情况
- 使用 `scripts/user-content-parser.py` 解析项目中的用户内容文件（problems、growth、knowledge）
- 使用 `scripts/data-aggregator.py` 聚合所有数据，支持 `--project-dir` 参数指定项目目录
- 参考 `references/data-extraction.md` 了解详细的数据提取方法

## 3. 组织周报结构
- 参考 `references/report-structure.md` 了解周报的标准结构
- 将数据组织成以下模块：
  - 数据统计（提交数、参与人数、完成事项等）
  - 本周进展（功能开发、问题修复、技术改进）
  - 本周遇到的问题
  - 本周个人成长
  - 相关知识分享
  - 下周计划
  - 风险与问题
  - 指令（Instructions）