"""提供可测试的模型参数选择策略。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    """描述一次模型调用应使用的稳定性与输出长度配置。"""

    temperature: float
    max_tokens: int


def select_generation_plan(message_count: int) -> GenerationPlan:
    """按对话长度选择模型生成参数，避免长对话无边界扩张输出。"""
    # 负数不是有效的消息数量，尽早失败比悄悄选择错误配置更容易定位问题。
    if message_count < 0:
        raise ValueError("Message count cannot be negative.")

    # 长对话优先选择更稳定、更受限的输出，降低成本与无关内容累积风险。
    if message_count > 10:
        return GenerationPlan(temperature=0.1, max_tokens=800)
    return GenerationPlan(temperature=0.2, max_tokens=1200)
