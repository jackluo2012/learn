# test_simple_agent.py
from dotenv import load_dotenv
# 配置好同级文件夹下.env中的大模型API, 可参考code文件夹配套的.env.example，也可以拿前几章的案例的.env文件复用。
from hello_agents import SimpleAgent, HelloAgentsLLM
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建SimpleAgent
agent = SimpleAgent(name="AI助手", llm=llm, system_prompt="你是一个有用的AI助手")
# 基础对话
response = agent.run("你好！请介绍一下自己")
print(response)
# 添加工具功能（可选）
from hello_agents.tools import CalculatorTool

calculator = CalculatorTool()
# 现在可以使用工具了
response = agent.run("请帮我计算 2 + 3 * 4")
print(response)

# 查看对话历史
print(f"历史消息数: {len(agent.get_history())}")
