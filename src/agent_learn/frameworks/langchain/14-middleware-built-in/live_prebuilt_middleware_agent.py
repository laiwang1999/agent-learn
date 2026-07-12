"""演示 SummarizationMiddleware 与 ModelCallLimitMiddleware 的真实 Agent 组合。"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, SummarizationMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


THREAD_ID = "chapter-14-prebuilt-middleware-demo"


@tool
def read_chapter_summary(chapter_number: int) -> dict[str, object]:
    """读取指定章节的学习摘要。

    Use when:
    - 用户询问某一章的学习重点或摘要。
    - 章节编号明确且在 1 到 14 之间。

    Do not use when:
    - 章节编号不明确或超出范围；应先澄清编号。

    Args:
        chapter_number: 章节编号，必须为 1 到 14 的整数。

    Returns:
        成功时: {"status": "success", "data": {"chapter_number": 0, "summary": "..."}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取进程内演示数据。

    Preconditions:
    - `chapter_number` 必须在有效范围内。

    Errors:
    - invalid_input: 章节编号不在 1 到 14 之间。
    - not_found: 不适用；范围内章节均存在。
    - permission_denied: 不适用。
    - external_service_error: 不适用。

    Examples:
        read_chapter_summary(chapter_number=14)

    Notes:
    - 只读且幂等；用于演示 prebuilt middleware 与多轮对话组合。
    """
    if chapter_number < 1 or chapter_number > 14:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Chapter number must be between 1 and 14."},
        }
    summaries = {
        13: "Middleware 是 Agent loop 内的横切控制层。",
        14: "Prebuilt Middleware 把常见控制能力沉到可复用组件。",
    }
    return {
        "status": "success",
        "data": {
            "chapter_number": chapter_number,
            "summary": summaries.get(chapter_number, "本章摘要待补充。"),
        },
    }


def create_prebuilt_middleware_agent():
    """创建挂载摘要与调用上限 middleware 的学习 Agent。"""
    summary_model = create_chat_model(temperature=0.1, max_tokens=400)
    return create_agent(
        model=create_chat_model(),
        tools=[read_chapter_summary],
        checkpointer=InMemorySaver(),
        middleware=[
            ModelCallLimitMiddleware(run_limit=12, thread_limit=24, exit_behavior="end"),
            SummarizationMiddleware(
                model=summary_model,
                trigger=("messages", 6),
                keep=("messages", 3),
            ),
        ],
        system_prompt=(
            "你是 Agent 学习助手。回答章节问题时必须调用 read_chapter_summary，"
            "禁止编造章节内容。最终答复必须使用中文。"
        ),
        name="prebuilt_middleware_agent",
    )


def build_thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """构造与 checkpointer 兼容的 thread 配置。"""
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        raise ValueError("Thread ID is required.")
    return {"configurable": {"thread_id": normalized_thread_id}}


def main() -> None:
    agent = create_prebuilt_middleware_agent()
    thread_config = build_thread_config(THREAD_ID)

    prompts = [
        "请介绍第 13 章的学习重点。",
        "第 14 章讲什么？",
        "再用一句话对比这两章。",
    ]

    for index, prompt in enumerate(prompts, start=1):
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            thread_config,
        )
        print(f"第 {index} 轮答复：", result["messages"][-1].content)
        print(f"第 {index} 轮消息数：", len(result["messages"]))


if __name__ == "__main__":
    main()
