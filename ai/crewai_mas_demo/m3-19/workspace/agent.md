# Agent 工作规范

## 工具使用说明

| 工具 | 用途 |
|------|------|
| BaiduSearchTool | 关键词搜索，获取初步结果和链接 |
| ScrapeWebsiteTool | 抓取网页详细内容（重要：搜索摘要不够，必须抓原文） |
| FileReadTool | 读取 workspace 中的任意文件（读记忆、读已有报告） |
| FileWriterTool | 写入 workspace 文件，写前必须先 FileReadTool 读取确认路径 |
| FixedDirectoryReadTool | 查看 workspace 目录结构，确认有哪些文件 |

## SOP：行业调研

1. 生成 3-5 组搜索关键词，用 BaiduSearchTool 搜索
2. 对排名靠前的结果用 ScrapeWebsiteTool 抓取原文（至少 2-3 个链接）
3. 整理成结构化报告：
   - 背景与定义
   - 当前现状（数据、玩家、规模）
   - 关键趋势
   - 结论与建议
4. 用 FileWriterTool 保存到 workspace/{主题}-调研报告.md

## SOP：周报生成

1. 用 FileReadTool 读取 workspace/memory.md，找"本周工作记录"区块
2. 按以下结构组织周报：
   - 本周完成：逐条列出，有数据的加数据
   - 下周计划：基于当前进度推断
   - 潜在风险：如有则列出
3. 风格严谨，不写废话，数据化表达
4. 用 FileWriterTool 保存到 workspace/周报-{日期}.md