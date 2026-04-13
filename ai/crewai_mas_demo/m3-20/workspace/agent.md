# Agent 工作规范

## 工具使用说明

本课（m3l20）主 Agent **不使用**文件读写工具（FileReadTool / FileWriterTool）。
所有文件操作通过 skill_loader 调用对应 Skill，由 Sub-Crew 在沙盒中执行。

| 工具 | 用途 |
|------|------|
| skill_loader | 调用 Skills 完成专项任务（memory-save / skill-creator / memory-governance）|

## 记忆治理触发规则

- memory.md 超过 150 行时主动提示用户触发 memory-governance
- 有死链（主题文件不存在但 memory.md 里有索引）时触发治理
- skills/ 有功能重叠的 Skill 时建议合并