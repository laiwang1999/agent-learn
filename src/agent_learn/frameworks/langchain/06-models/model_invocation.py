"""演示模型初始化、`invoke` 与运行时生成参数选择。"""

from langchain_core.messages import HumanMessage, SystemMessage

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model
from agent_learn.frameworks.langchain.model_policy import select_generation_plan


SYSTEM_PROMPT = """你是一名 Agent 工程学习助手。
请使用中文回答，先给出结论，再说明关键依据。无法验证的信息必须明确说明限制。"""


def build_messages(question: str) -> list[SystemMessage | HumanMessage]:
    """为一次独立模型调用构造中文系统提示与用户消息。"""
    # 空问题没有可推理内容，先拒绝可以避免无意义的模型调用和费用。
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question.strip())]


def create_instruction_model(message_count: int):
    """按照对话长度选择生成参数并创建对话模型。"""
    plan = select_generation_plan(message_count)
    # 参数策略与 provider 适配器分开，使模型选择逻辑可独立测试。
    return create_chat_model(temperature=plan.temperature, max_tokens=plan.max_tokens)


def main() -> None:
    model = create_instruction_model(message_count=1)
    response = model.invoke(build_messages("请用三句话解释 Agent 中模型和工具的分工。"))
    print(response.text)


if __name__ == "__main__":
    main()
