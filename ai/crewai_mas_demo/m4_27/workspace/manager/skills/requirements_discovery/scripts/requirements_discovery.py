#!/usr/bin/env python3
"""
需求澄清脚本 - Agent 通过 Bash 在沙盒中调用。

功能：
1. 分析项目需求（四个维度：目标、边界、约束、风险）
2. 生成需求文档
3. 写入 /mnt/shared/needs/requirements.md

沙盒内调用示例：
  python3 /workspace/skills/requirements_discovery/scripts/requirements_discovery.py \\
      --project-desc "宠物健康记录App，支持多宠物管理和疫苗提醒"
"""

import argparse
import json
from pathlib import Path


def analyze_requirements(project_desc: str) -> dict:
    """
    分析项目需求，生成四个维度的信息。

    这是一个示例实现，实际中应该使用 LLM 来分析。
    """

    # 提取关键信息（简化版）
    requirements = {
        "project_background": project_desc,
        "objectives": {
            "problem": "待明确：需要解决的核心问题是什么？",
            "success_criteria": "待明确：成功的标准是什么？",
        },
        "boundaries": {
            "in_scope": [
                "待明确：哪些功能在范围内？",
            ],
            "out_of_scope": [
                "待明确：哪些功能明确不做？",
            ],
        },
        "constraints": {
            "time": "待明确：时间限制？",
            "technology": "待明确：技术栈限制？",
            "resources": "待明确：资源限制？",
        },
        "risks": [
            "待明确：已知风险或不确定性？",
        ],
        "clarification_needed": [
            "问题1：目标用户群体是什么？",
            "问题2：核心功能优先级？",
            "问题3：是否有特殊的技术或业务约束？",
        ],
    }

    # 如果描述包含常见关键词，进行简单推断
    if "App" in project_desc or "app" in project_desc:
        requirements["constraints"]["technology"] = "移动应用（iOS/Android）"
        requirements["objectives"]["problem"] = "用户需要便捷的方式来管理和记录特定信息"

    if "管理" in project_desc:
        requirements["boundaries"]["in_scope"].append("信息管理功能（增删改查）")
        requirements["boundaries"]["in_scope"].append("数据持久化存储")

    if "提醒" in project_desc:
        requirements["boundaries"]["in_scope"].append("通知提醒功能")
        requirements["clarification_needed"].append("问题：提醒方式（推送/短信/邮件）？")

    return requirements


def generate_requirements_md(requirements: dict) -> str:
    """生成 Markdown 格式的需求文档。"""

    lines = [
        "# 项目需求文档",
        "",
        "## 项目背景",
        requirements["project_background"],
        "",
        "## 目标",
        "",
        "### 要解决的问题",
        f"- {requirements['objectives']['problem']}",
        "",
        "### 成功标准",
        f"- {requirements['objectives']['success_criteria']}",
        "",
        "## 边界",
        "",
        "### 范围内",
    ]

    for item in requirements["boundaries"]["in_scope"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "### 范围外",
    ])

    for item in requirements["boundaries"]["out_of_scope"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 约束",
        "",
        f"- 时间：{requirements['constraints']['time']}",
        f"- 技术：{requirements['constraints']['technology']}",
        f"- 资源：{requirements['constraints']['resources']}",
        "",
        "## 风险",
        "",
    ])

    for risk in requirements["risks"]:
        lines.append(f"- {risk}")

    lines.extend([
        "",
        "## 待澄清（需 Human 确认）",
        "",
    ])

    for i, q in enumerate(requirements["clarification_needed"], 1):
        lines.append(f"{i}. {q}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="需求澄清脚本 - 分析需求并生成需求文档")
    parser.add_argument("--project-desc", required=True, help="项目需求描述")
    parser.add_argument("--output-path", default="/mnt/shared/needs/requirements.md",
                       help="需求文档输出路径（默认：/mnt/shared/needs/requirements.md）")
    args = parser.parse_args()

    # 分析需求
    requirements = analyze_requirements(args.project_desc)

    # 生成 Markdown 文档
    content = generate_requirements_md(requirements)

    # 确保输出目录存在
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    output_path.write_text(content, encoding="utf-8")

    # 返回结果
    result = {
        "errcode": 0,
        "data": {
            "output_file": str(output_path),
            "file_size": len(content),
            "clarification_count": len(requirements["clarification_needed"]),
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
