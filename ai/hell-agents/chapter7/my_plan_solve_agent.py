# 默认规划器提示词模板
DEFAULT_PLANNER_PROMPT = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

# 默认执行器提示词模板
DEFAULT_EXECUTOR_PROMPT = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""
from typing import Optional, Dict

from hello_agents import PlanAndSolveAgent, HelloAgentsLLM, Config


class MyPlanAndSolveAgent(PlanAndSolveAgent):
    """自定义计划求解智能体，支持可插拔的提示词模板。"""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        planner_prompt: Optional[str] = None,
        executor_prompt: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
    ):
        """初始化计划求解智能体。"""
        # 兼容 custom_prompts，同时支持直接传入 planner_prompt 与 executor_prompt
        prompts = custom_prompts.copy() if custom_prompts else {}
        if planner_prompt is not None:
            prompts["planner"] = planner_prompt
        if executor_prompt is not None:
            prompts["executor"] = executor_prompt

        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config,
            custom_prompts=prompts if prompts else None,
        )
        template_info = []
        if prompts:
            template_info.append("自定义")
        else:
            template_info.append("默认")
        print(f"✅ {name} 初始化完成，提示词模板: {'/'.join(template_info)}")

    def run(
        self,
        input_text: str,
        planner_prompt: Optional[str] = None,
        executor_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """运行计划求解过程并输出最终结果。"""
        # 如果没有传入单独模板，则使用默认模板
        self.planner.prompt_template = planner_prompt or DEFAULT_PLANNER_PROMPT
        self.executor.prompt_template = executor_prompt or DEFAULT_EXECUTOR_PROMPT

        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")
        result = super().run(input_text, **kwargs)
        return result
