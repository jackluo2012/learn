"""
课程：16｜Skills 生态：让 Agent 接入大量工具
统一示例文件：m2l16_skills.py

使用前准备：
- 在项目根目录运行 sandbox-docker-compose.yaml 启动 AIO-Sandbox
- 将输入 PDF 放在 workspace/data 下（容器内路径：/workspace/data）
- 输出结果会写到 workspace/output 下（容器内路径：/workspace/output）

包含：
- build_skill_crew：Sub-Crew 工厂（由 SkillLoaderTool 内部调用）
- build_main_crew：主协调 Crew 工厂（持有 SkillLoaderTool）
- run_doc_flow：异步调用入口（给 FastAPI 用）
- main / main_async：命令行演示入口
"""

import asyncio
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task

# 将 m2l16/ 和项目根加入 sys.path，便于导入 llm 和 tools
_M2L16_ROOT = Path(__file__).parent
_PROJECT_ROOT = _M2L16_ROOT.parent
for _p in [str(_M2L16_ROOT), str(_PROJECT_ROOT)]:
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

from llm.aliyun_llm import AliyunLLM  # noqa: E402
from tools.skill_loader_tool import SkillLoaderTool, build_skill_crew  # noqa: E402
from tools.intermediate_tool import IntermediateTool  # noqa: E402
# Demo 用户请求
USER_REQUEST = (
    "请将./workspace/data/quarterly_report.pdf里的关键数据提炼出来，生成一份格式规范的 Word 文档"
)        


# ── 主 Crew 工厂：协调者 + SkillLoaderTool ───────────────────────────────────

def build_main_crew() -> Crew:
    """
    工厂函数：每次调用创建全新实例。
    SkillLoaderTool 在此实例化，__init__ 会自动解析 skills 元数据、构建 XML description。
    """
    skill_loader = SkillLoaderTool()
    #rint(f"SkillLoaderTool 初始化完成，解析到的技能有：{skill_loader.description}")
    #eturn
    orchestrator = Agent(
        role="skill使用助手总管",
        goal="根据用户需求进行分析，拆解，分发任务，最终保证任务的完成",
        backstory="""
        你是skill使用助手总管，善于接收用户的需求，使用skill去完成。

        你通常的工作思路包括：
        1、你会先去理解用户需求，进行需求分析，将结果使用Save_Intermediate_Product_Tool记录；
        2、当要完成任务有需要参考的type是reference的skill时，你需要使用skill_loader工具去加载对应skill；
        3、你会规划步骤，生成子任务，使用Save_Intermediate_Product_Tool记录，每个子任务都要有明确的预期目标和足够的背景信息；
        3、然后依次完成子任务，当子任务适合type是task的skill完成时，你会生成task_context并使用skill_loader工具，调用对应skill去完成；预期目标应该是结构化的json结果，你必须给子任务一个json schema，以便你确认执行情况和结果；
        4、根据每次的子任务结果，你会去管理当前的步骤，如果出现偏差你可以进行重新规划，同样使用Save_Intermediate_Product_Tool记录；
        5、最终你会将最终结果返回给用户。

        行为边界：
        你会尽量使用skill完成任务，而不是自行编造结果。
        """,
        llm=AliyunLLM(region="cn", temperature=0.3),
        tools=[skill_loader, IntermediateTool()],
        verbose=True,
    )

    main_task = Task(
        description="{user_request}",
        expected_output=(
            "完整的任务执行报告，包含：\n"
            "- 每个 Skill 的执行结果\n"
            "- 最终输出文件路径\n"
            "- 任务是否成功完成"
        ),
        agent=orchestrator,
    )

    return Crew(
        agents=[orchestrator],
        tasks=[main_task],
        process=Process.sequential,
        verbose=True,
    )


# ── FastAPI / 异步调用入口 ────────────────────────────────────────────────────

async def run_doc_flow(user_request: str) -> tuple[str | None, str]:
    """
    对外异步入口，供 FastAPI service 层 await 调用。
    asyncio.wait_for 加 300s 超时，防止文档处理任务无限阻塞。

    Returns:
        (result_str, "")        成功时
        (None, error_message)   失败时
    """
    crew = build_main_crew()
    try:
        result = await asyncio.wait_for(
            crew.akickoff(inputs={"user_request": user_request}),
            timeout=300,
        )
        return str(result), ""
    except Exception as exc:  # noqa: BLE001
        return None, f"流程执行失败: {type(exc).__name__}: {exc}"


# ── 命令行演示入口 ─────────────────────────────────────────────────────────────

def main():
    """同步入口：适用于命令行直接运行"""
    print("=" * 60)
    print("16课 Skills 生态 Demo：PDF → DOCX")
    print("=" * 60)
    print(f"\n用户请求：{USER_REQUEST}\n")

    crew = build_main_crew()
    
   
    result = crew.kickoff(inputs={"user_request": USER_REQUEST})

    print("\n" + "=" * 60)
    print("执行结果：")
    print(result)
    print("=" * 60)


async def main_async():
    """异步入口：与 FastAPI 调用链一致，用于验证 akickoff 路径"""
    print("=" * 60)
    print("16课 Skills 生态 Demo（异步模式）：PDF → DOCX")
    print("=" * 60)

    result, error = await run_doc_flow(USER_REQUEST)

    if error:
        print(f"\n执行失败：{error}")
    else:
        print(f"\n执行结果：\n{result}")


if __name__ == "__main__":
    # 默认同步运行；传入 --async 参数则用异步模式
    if "--async" in sys.argv:
        asyncio.run(main_async())
    else:
        main()