"""演示 checkpointer 与 `thread_id` 如何在真实 Agent 多轮调用中保持短期记忆。"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


THREAD_ID = "chapter-09-thread-memory-demo"


def create_thread_memory_agent():
    """创建带 InMemorySaver 的学习 Agent，用于观察同 thread 内的上下文连续性。"""
    # InMemorySaver 仅用于本地学习；生产应替换为数据库-backed checkpointer。
    return create_agent(
        model=create_chat_model(),
        tools=[],
        system_prompt=(
            "你是学习助手。记住用户在当前对话中主动提供的名字，并在后续问题中正确引用。"
            "如果用户尚未提供名字，应明确说明还不知道。最终答复必须使用中文。"
        ),
        checkpointer=InMemorySaver(),
        name="thread_memory_agent",
    )


def build_thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """构造与 LangChain Agent 调用兼容的 thread 配置。"""
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        raise ValueError("Thread ID is required.")
    return {"configurable": {"thread_id": normalized_thread_id}}


def main() -> None:
    agent = create_thread_memory_agent()
    thread_config = build_thread_config(THREAD_ID)

    # 第一轮：用户自我介绍；state 会写入 checkpointer。
    first_result = agent.invoke(
        {"messages": [{"role": "user", "content": "你好，我叫 Bob。"}]},
        thread_config,
    )
    print("第一轮答复：", first_result["messages"][-1].content)

    # 第二轮：同一 thread_id 应能读取前文，而不是重新失忆。
    second_result = agent.invoke(
        {"messages": [{"role": "user", "content": "我叫什么名字？"}]},
        thread_config,
    )
    print("第二轮答复：", second_result["messages"][-1].content)


if __name__ == "__main__":
    main()
