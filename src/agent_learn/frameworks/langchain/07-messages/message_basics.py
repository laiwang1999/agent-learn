"""演示 LangChain Messages 的角色、内容与元数据边界。"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


SYSTEM_PROMPT = """你是一名 Agent 工程学习助手。
请使用中文回答，并把可验证事实、推断和不确定性区分开。最终答复必须使用中文。"""


def build_message_history(question: str) -> list[BaseMessage]:
    """构造包含系统约束、用户问题和模型回答的最小消息历史。"""
    # 用户问题属于模型可见输入；空问题没有可推理内容，应在构造上下文前失败。
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question cannot be empty.")

    # 为每条教学消息指定稳定 ID，便于把 UI、trace 和后续调试记录关联到同一条上下文。
    return [
        SystemMessage(content=SYSTEM_PROMPT, id="system_learning_assistant"),
        HumanMessage(content=normalized_question, id="user_message_001"),
        AIMessage(
            content="LangChain 使用有序的 Message 列表向模型提供上下文。",
            id="assistant_message_001",
            usage_metadata={"input_tokens": 18, "output_tokens": 16, "total_tokens": 34},
        ),
    ]


def describe_message(message: BaseMessage) -> dict[str, str]:
    """提取适合日志和教学输出的稳定消息摘要。"""
    # content 允许 provider 使用结构化块；本示例只摘要文本，避免把未知原始负载误当作用户可读文本。
    content = message.content if isinstance(message.content, str) else str(message.content)
    return {"type": message.type, "id": message.id or "", "content": content}


def main() -> None:
    messages = build_message_history("为什么 Agent 需要使用 Message 列表管理上下文？")
    for message in messages:
        overview = describe_message(message)
        print(f"{overview['type']} ({overview['id']}): {overview['content']}")

    # usage_metadata 常来自真实 provider 的 AIMessage；这里使用固定值演示成本观测字段的位置。
    assistant_message = messages[-1]
    assert isinstance(assistant_message, AIMessage)
    print(f"token 用量：{assistant_message.usage_metadata}")


if __name__ == "__main__":
    main()
