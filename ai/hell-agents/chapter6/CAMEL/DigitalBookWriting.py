from colorama import Fore
from camel.societies import RolePlaying
from camel.utils import print_text_animated
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from dotenv import load_dotenv
import os

load_dotenv()
# Some versions of camel expect QWEN_API_KEY to be set as an env var even if an api_key is passed in
if not os.getenv("QWEN_API_KEY") and os.getenv("LLM_API_KEY"):
    os.environ["QWEN_API_KEY"] = os.getenv("LLM_API_KEY")

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID")
print(LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_ID)

# 创建模型,在这里以Qwen为例,调用的百炼大模型平台API
# 通过环境变量配置 OpenAI 客户端
os.environ["OPENAI_API_KEY"] = LLM_API_KEY
os.environ["OPENAI_BASE_URL"] = LLM_BASE_URL

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=LLM_MODEL_ID,
)

# 定义协作任务
task_prompt = """
创作一本关于"拖延症心理学"的短篇电子书，目标读者是对心理学感兴趣的普通大众。
要求：
1. 内容科学严谨，基于实证研究
2. 语言通俗易懂，避免过多专业术语
3. 包含实用的改善建议和案例分析
4. 篇幅控制在8000-10000字
5. 结构清晰，包含引言、核心章节和总结
"""
print(Fore.YELLOW + f"协作任务:\n{task_prompt}\n")

# 初始化角色扮演会话
# AI 作家作为 "user"，负责提出写作结构和要求
# AI 心理学家作为 "assistant"，负责提供专业知识和内容
role_play_session = RolePlaying(
    assistant_role_name="心理学家",
    user_role_name="作家",
    task_prompt=task_prompt,
    model=model,
    with_task_specify=False,  # 在本例中，我们直接使用给定的task_prompt
    # 增加超时时间到10分钟
    assistant_agent_kwargs={"step_timeout": 600},
    user_agent_kwargs={"step_timeout": 600},
)

print(Fore.CYAN + f"具体任务描述:\n{role_play_session.task_prompt}\n")

# 开始协作对话
chat_turn_limit, n = 30, 0
# 调用 init_chat() 来获得由 AI 生成的初始对话消息
input_msg = role_play_session.init_chat()

while n < chat_turn_limit:
    n += 1
    try:
        # step() 方法驱动一轮完整的对话，AI 用户和 AI 助理各发言一次
        assistant_response, user_response = role_play_session.step(input_msg)

        # 检查是否有消息返回，防止对话提前终止
        if assistant_response.msg is None or user_response.msg is None:
            break

        print_text_animated(Fore.BLUE + f"作家 (AI User):\n\n{user_response.msg.content}\n")
        print_text_animated(
            Fore.GREEN + f"心理学家 (AI Assistant):\n\n{assistant_response.msg.content}\n"
        )

        # 检查任务完成标志
        if (
            "<CAMEL_TASK_DONE>" in user_response.msg.content
            or "<CAMEL_TASK_DONE>" in assistant_response.msg.content
        ):
            print(Fore.MAGENTA + "✅ 电子书创作完成！")
            break

        # 将助理的回复作为下一轮对话的输入
        input_msg = assistant_response.msg
    except TimeoutError as e:
        print(Fore.RED + f"⚠️ 第 {n} 轮对话超时: {e}")
        print(Fore.YELLOW + "提示：已生成的内容已保存，可以稍后继续或手动编辑")
        break
    except Exception as e:
        print(Fore.RED + f"⚠️ 第 {n} 轮对话出错: {e}")
        print(Fore.YELLOW + "继续下一轮...")
        continue

print(Fore.YELLOW + f"总共进行了 {n} 轮协作对话")
