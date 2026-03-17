from typing import Optional, Dict

from hello_agents import ReflectionAgent, HelloAgentsLLM, Config


class MyReflectionAgent(ReflectionAgent):
    """自定义反思智能体，支持可插拔的提示词模板。"""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None,
    ):
        """初始化反思智能体。"""
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config,
            max_iterations=max_iterations,
            custom_prompts=custom_prompts,
        )
        print(f"✅ {name} 初始化完成，最大迭代次数: {max_iterations}")

    def run(self, input_text: str, **kwargs) -> str:
        """运行反思过程并输出最终结果。"""
        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")
        result = super().run(input_text, **kwargs)
        return result
