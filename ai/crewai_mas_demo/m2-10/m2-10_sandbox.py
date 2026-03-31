"""
课程：15｜王牌超能力：代码解释器与无头浏览器 示例代码
沙盒 Agent + MCP 工具一体化实战

运行程序前需要先安装docker并启动AIO-Sandbox：
docker run --security-opt seccomp=unconfined --rm -it -p 8022:8080 ghcr.io/agent-infra/sandbox:latest
# 拉取并运行最新版本
docker run --security-opt seccomp=unconfined --rm -it -p 8022:8080 ghcr.io/agent-infra/sandbox:latest
本示例演示如何在 CrewAI 中：
1. 定义一个具备「代码执行 + 文件系统 + 无头浏览器」多重能力的万能沙盒 Agent
2. 通过 MCP HTTP Server 将沙盒中的浏览器、代码执行环境等能力暴露给 Agent 调用
3. 利用 Pydantic 定义结构化输出模型，约束 Agent 的最终交付物格式
4. 通过 Task / Crew 组合，驱动 Agent 完成一个端到端的量化分析 + 新闻研读任务

学习要点：
- 如何在 Agent 中挂载 MCP Server，让模型拥有「外接超能力」
- 如何用自然语言在 backstory 中教会 Agent 合理使用代码解释器与无头浏览器
- 如何用 Pydantic 模型约束复杂、多字段的分析报告输出
- 如何通过 Task description 设计一个真实、可执行的金融类分析场景
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# ==============================================================================
# 环境与依赖配置：将项目根目录加入 Python 路径
# ==============================================================================
project_root = Path(__file__).resolve().parent.parent
print(project_root)
sys.path.insert(0, str(project_root))

from crewai import Agent, Task, Crew, Process
from llm import aliyun_llm
from crewai.mcp import MCPServerStdio, MCPServerHTTP, MCPServerSSE
from crewai.mcp.filters import create_static_tool_filter, create_dynamic_tool_filter, ToolFilterContext

from pydantic import BaseModel, Field
from typing import List

from tools.intermediate_tool import IntermediateTool

# ==============================================================================
# Agent 定义：万能沙盒工作助手（代码解释器 + 无头浏览器）
# ==============================================================================
# 该 Agent 通过 MCP HTTP Server 连接到沙盒环境，拥有：
# - 浏览器能力：通过无头浏览器访问网页、搜索信息、抓取数据
# - 代码执行能力：在沙盒中运行 Python/JS 完成量化分析或数据清洗
# - 文件系统能力：读写中间结果，形成「可追溯」的工作流
# backstory 中用中文详细约束了使用这些工具时的习惯和步骤，让 Agent 更像一个有自我工作流的助理。
sandbox_agent = Agent(
    role="万能沙盒工作助手",
    goal="利用沙盒的浏览器、文件系统、代码执行环境，尝试各种方式最终完成任务",
    backstory="""
    你拥有熟练的python和js的编程技术，擅长使用各种工具和环境来完成任务。

    你有如下专业知识：
    你现在在国内，搜索引擎使用百度，搜索引擎使用方式为：https://www.baidu.com/s?wd=你的问题
    你熟悉浏览器操作，可以使用浏览器来完成各种任务，不过因为你没有手机，通常没法用手机登录；浏览器有时执行很慢，你需要多等待；
    你非常善于进行代码编辑，当遇到的问题需要代码解决时，你会使用代码编辑器来完成任务；如果遇到代码执行问题，你也会通过网络搜索查询解决；
    当你需要一些数据和功能时，你也会尝试搜索对应的api接口或者sdk来完成任务；
    你也可以用系统命令安装依赖库；
    你很善用文件系统，你会自己记录中间结果，阅读之前的进度，查看代码或者浏览器生成的结果等，你相信好记性不如烂笔头；
    
    当你收到任务时，你通常习惯按照以下思路完成任务：
    1、你会先去理解任务，进行需求分析，当任务中有任何疑问，你会使用百度搜索来明确任务；
    2、之后你会根据任务需求，基于你能使用的工具，设计一个大致的解决方案步骤列表，并通过写入沙盒文件的方式先进行记录；
    3、之后你会按照步骤列表逐步执行，每完成一个步骤，你会将结果写入沙盒文件中记录；
    4、当执行中发现偏离步骤列表，你会及时调整步骤列表，并继续执行；
    5、当任务完成后，你会将最终结果返回给用户；
    """,
    # MCPServerHTTP 将沙盒暴露为一个远程工具服务器，Agent 通过该通道调用浏览器/代码执行等工具
    mcps=[
        MCPServerHTTP(
            url="http://localhost:8080/mcp",  # MCP 服务器地址（沙盒统一入口）
            streamable=True,  # 支持流式响应，提升交互体验
            cache_tools_list=True,  # 缓存工具列表，提高多次调用场景下的性能
        )
    ],
    llm=aliyun_llm.AliyunLLM(
        model="qwen3-max",
        api_key=os.getenv("QWEN_API_KEY"),
        region="cn",
    ),
    tools=[], # crewai有个bug，如果tools是None，不加载mcp，所以这里需要加一个空列表
    allow_delegation=False,
    # 将迭代次数调高，使其有足够回合通过代码解释器+浏览器完成复杂任务
    max_iter=100,
)
# crewai的bug，委派时走 execute_task，不会调用 _prepare_kickoff，MCP 不会自动加载，需在首次执行前手动加载
if sandbox_agent.mcps:
    _mcp_tools = sandbox_agent.get_mcp_tools(sandbox_agent.mcps)
    if _mcp_tools:
        sandbox_agent.tools.extend(_mcp_tools)

assistant_agent = Agent(
    role="个人万能助手总管",
    goal="根据用户需求进行分析，拆解，分发任务，最终保证任务的完成",
    backstory="""
    你是个人万能助手总管，善于接收用户的需求，拆解后分发给其它agent去完成。

    你下属的agent包括：
    - 万能沙盒工作助手：利用沙盒的浏览器、文件系统、代码执行环境，尝试各种方式最终完成任务。当你需要使用代码、浏览器、搜索时，都要委托给万能沙盒工作助手去完成。

    你通常的工作思路包括：
    1、你会先去理解用户需求，进行需求分析，将结果使用Save_Intermediate_Product_Tool记录；
    2、之后你会规划步骤，生成子任务，使用Save_Intermediate_Product_Tool记录，每个子任务都要有明确的预期目标和足够的背景信息；
    3、然后依次将子任务委托给其它agent，直到所有子任务完成。预期目标应该是结构化的json结果，你必须给子任务一个json schema，以便你整合和拼接最终结果；
    4、根据每次的子任务结果，你会去管理当前的步骤，如果出现偏差你可以进行重新规划，同样使用Save_Intermediate_Product_Tool记录；
    5、最终你会将最终结果返回给用户。

    行为边界：
    你不会直接执行任务，你会将任务拆解后分发给其它agent去完成。
    你必须完全参照子任务的执行结果，不能自行编造，如果有疑问你需要重新分配任务去完成；
    """,
    allow_delegation=True,
    tools=[IntermediateTool()],
    llm=aliyun_llm.AliyunLLM(
        model="qwen3-max",
        api_key=os.getenv("QWEN_API_KEY"),
        region="cn",
    ),
    max_iter=100,
)        
# ==============================================================================
# 数据模型定义：量化行情 + 舆情驱动的早盘报告
# ==============================================================================
class KlineData(BaseModel):
    """单日 K 线数据结构，用于后续在沙盒中做量化分析"""

    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
class LatestData(BaseModel):
    """
    阿里巴巴港股最新的量化行情数据结构

    这里专门抽象出一个 latest_data 模块，方便：
    - 在沙盒中用代码解释器对结构化行情做统计分析
    - 在最终报告中引用精简后的关键指标，而不是直接输出原始接口响应
    """

    latest_price: float = Field(
        ...,
        description="最新股价，单位为港币，需对应早盘时点的最新成交价",
    )
    latest_volume: int = Field(
        ...,
        description="当日最新成交量，单位为股，用于衡量当前交易活跃度",
    )
    latest_market_cap: float = Field(
        ...,
        description="最新市值，单位为港币，基于最新股价和总股本计算",
    )
    latest_pe_ratio: float = Field(
        ...,
        description="最新市盈率（PE），用于衡量当前估值相对盈利水平的高低",
    )
    last_30_days_klines: List[KlineData] = Field(
        ...,
        description="最近30个交易日的日 K 线数据列表，用于后续量化分析",
    )
class AlibabaMorningReport(BaseModel):
    """
    阿里巴巴港股早盘分析报告——本任务的最终交付物结构

    这个模型约束了 Agent 在长流程中最终必须给出的结构化结果，确保：
    - 量化分析（代码解释器产出）和舆情分析（浏览器产出）能够被融合成一个统一对象
    - 下游如果要做自动发送/归档/二次加工时，不需要再对自然语言做复杂解析
    """

    today: str = Field(
        ...,
        description="报告日期，使用 YYYY-MM-DD 格式，例如：2026-02-23",
    )
    latest_data: LatestData = Field(
        ...,
        description="基于最新行情和最近30日 K 线整理出的结构化量化数据，用于支撑后续分析结论",
    )
    quantitative_analysis: str = Field(
        ...,
        description=(
            "基于 latest_data 中的量化指标（如涨跌幅、波动率、成交量变化、市值和市盈率区间等）"
            "给出条理清晰的量化分析结论，需包含：当前价格所处位置、短期趋势判断、"
            "风险/机会点，要求用专业、简明的中文表述，分段或分点说明"
        ),
    )
    sentiment_analysis: str = Field(
        ...,
        description=(
            "基于最近的新闻资讯、市场评论和舆情信息，总结对阿里巴巴的利好/利空因素，"
            "以及整体市场情绪（偏乐观/中性/悲观），需给出主要新闻要点及其可能影响"
        ),
    )
    final_report: str = Field(
        ...,
        description=(
            "一封面向普通投资者的完整早盘报告正文，需以今天的日期开头，"
            "自然融合最新行情、量化分析结论和舆情解读，形成一个结构清晰、"
            "逻辑严谨、可直接发送的早报文本（使用正式、客观、中文口吻）"
        ),
    )

# ==============================================================================
# Task 定义：驱动沙盒 Agent 完成端到端早盘分析
# ==============================================================================
# 该 Task 会在执行过程中，引导 Agent：
# 1. 利用「代码解释器」能力抓取并计算阿里巴巴港股的量化指标和 K 线特征
# 2. 利用「无头浏览器」能力搜索最新新闻、舆情，并做利好/利空归纳
# 3. 将两部分结果融合，按 AlibabaMorningReport 的结构输出最终早盘报告    

task = Task(
    description=(
        "今天是 {today}。你需要作为我的阿里巴巴港股“个人工作助理”，完成一个早盘报告里程碑任务："
        "1）基于沙盒可用的浏览器和代码执行能力，获取阿里巴巴港股（例如 9988.HK）的最新行情数据和最近 30 个交易日的 K 线数据(https://finance.yahoo.com 数据比较全)；重要：你的所有数据都必须是真实数据，要想法获取，实在不能获取宁可失败也不能编造"
        "2）使用 Python 在沙盒中对这些数据进行量化分析（如价格区间、涨跌幅、成交量变化、市值和市盈率水平、K线形态、趋势线、支撑阻力位等），你的所有结论必须经过计算，不能编造"
        "并据此形成清晰的量化分析结论；"
        "3）通过浏览器检索阿里巴巴的最新新闻资讯和市场评论（在国内环境下优先使用百度搜索，例如：https://www.baidu.com/s?wd=阿里巴巴 港股 新闻），你的新闻必须附上来源且符合真实信息，不能自己加工"
        "提炼对股价可能产生影响的关键信息并判断利好/利空及市场情绪；"
        "4）在完成以上准备工作后，整合量化分析与舆情结论，撰写一封可以直接发送给投资者阅读的阿里巴巴港股早盘分析报告。"
    ),
    expected_output=(
        "严格符合 AlibabaMorningReport Pydantic 模型结构的 JSON 输出："
        "必须完整填充 today、latest_data、quantitative_analysis、sentiment_analysis、final_report 五个字段；"
        "其中 latest_data 使用结构化数值数据，其余字段为中文自然语言描述。"
    ),
    agent=assistant_agent,
    output_pydantic=AlibabaMorningReport,
)
# ==============================================================================
# Crew 定义与启动：单 Agent 顺序流程
# ==============================================================================
# 这里使用 Process.sequential 虽然只有一个 Task，但保持与多任务场景一致的写法，
# 方便后续扩展更多里程碑任务（例如增加复盘、风控建议等）。
crew = Crew(
    agents=[assistant_agent, sandbox_agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,
)
# 统一在入口处构造 today 入参，保证「可复现性」和「可观测性」
today_str = datetime.now().strftime("%Y-%m-%d")
crew.kickoff(inputs={"today": today_str})