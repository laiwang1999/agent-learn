"""演示真实模型调用返回的 `AIMessage` 与消息历史结构。"""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


SYSTEM_PROMPT = """你是一名 Agent 工程学习助手。
请使用中文回答，回答应简洁准确。无法验证的信息必须明确说明限制。"""


def build_instruction_messages(question: str) -> list[SystemMessage | HumanMessage]:
    """构造一次模型调用所需的消息列表。"""
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question cannot be empty.")
    return [
        SystemMessage(content=SYSTEM_PROMPT, id="system_message_001"),
        HumanMessage(content=normalized_question, id="human_message_001"),
    ]


def describe_message(message: BaseMessage) -> dict[str, object]:
    """提取消息类型、内容与可用的 usage 元数据。"""
    summary: dict[str, object] = {
        "type": message.type,
        "id": message.id,
        "content": message.content,
    }
    if isinstance(message, AIMessage) and message.usage_metadata is not None:
        summary["usage_metadata"] = message.usage_metadata
    return summary


def create_message_demo_agent():
    """创建无工具 Agent，用于观察运行结束后的完整 messages 历史。"""
    return create_agent(
        model=create_chat_model(),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        name="message_demo_agent",
    )


def main() -> None:
    # 第一步：直接模型调用，观察 provider 返回的 AIMessage 结构。
    model = create_chat_model()
    direct_response = model.invoke(
        build_instruction_messages("请用一句话说明 ToolMessage 中 tool_call_id 的作用。")
    )
    print("直接模型调用：", describe_message(direct_response))

    # 第二步：通过 Agent harness 运行，观察 state 中累积的 messages 序列。
    agent = create_message_demo_agent()
    agent_result = agent.invoke(
        {"messages": [{"role": "user", "content": "请用一句话说明 messages 在 Agent 中的作用。"}]}
    )
    print("Agent 消息历史：")
    for message in agent_result["messages"]:
        print(describe_message(message))


if __name__ == "__main__":
    main()
