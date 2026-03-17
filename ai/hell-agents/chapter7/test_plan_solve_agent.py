from dotenv import load_dotenv
from hello_agents.core.llm import HelloAgentsLLM
from my_plan_solve_agent import MyPlanAndSolveAgent

# 加载环境变量
load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建自定义PlanAndSolveAgent
agent = MyPlanAndSolveAgent(name="我的规划执行助手", llm=llm)

# 测试复杂问题
question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"

# result = agent.run(question)
# print(f"\n最终结果: {result}")

# # 查看对话历史
# print(f"对话历史: {len(agent.get_history())} 条消息")


# 创建专门用于数学问题的自定义提示词
math_prompts = {
    "planner": """
你是数学问题规划专家。请将数学问题分解为计算步骤:

问题: {question}

输出格式:
python
["计算步骤1", "计算步骤2", "求总和"]

""",
    "executor": """
你是数学计算专家。请计算当前步骤:

问题: {question}
计划: {plan}
历史: {history}
当前步骤: {current_step}

请只输出数值结果:
""",
}

# 使用自定义提示词创建数学专用Agent
math_agent = MyPlanAndSolveAgent(
    name="数学计算助手", llm=llm, custom_prompts=math_prompts
)

# 测试数学问题
math_result = math_agent.run(question)
print(f"数学专用Agent结果: {math_result}")
