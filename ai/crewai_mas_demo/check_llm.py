from crewai import BaseLLM
from llm.aliyun_llm import AliyunLLM
print("AliyunLLM bases:", AliyunLLM.__bases__)
print("Is subclass of BaseLLM:", issubclass(AliyunLLM, BaseLLM))

# Check if AliyunLLM has the required methods
for method in ['call', '_call', 'supports_system_prompt', 'supports_stop_words', 'supports_function_calling', 'supports_vision']:
    print(f"Has {method}: {hasattr(AliyunLLM, method)}")