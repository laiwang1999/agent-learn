"""演示真实 Agent 的底层 `stream_mode`：`updates` 与 `messages`（v2）。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from langchain.agents import create_agent

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


def _load_basic_tool_definition_module():
    """加载第 8 章天气工具，复用既有 tool schema。"""
    module_path = Path(__file__).parents[1] / "08-tools" / "basic_tool_definition.py"
    spec = spec_from_file_location("basic_tool_definition", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


get_city_weather = _load_basic_tool_definition_module().get_city_weather


def create_stream_modes_agent():
    """创建用于底层 streaming 演示的天气 Agent。"""
    return create_agent(
        model=create_chat_model(),
        tools=[get_city_weather],
        system_prompt=(
            "你是天气助手。回答天气问题时必须调用 get_city_weather，禁止猜测天气事实。"
            "最终答复必须使用中文。"
        ),
        name="stream_modes_weather_agent",
    )


def consume_v2_stream_chunk(chunk: dict[str, object]) -> None:
    """按 v2 StreamPart 的 `type` 打印 updates 或 messages 信息。"""
    chunk_type = chunk.get("type")
    data = chunk.get("data")

    if chunk_type == "updates" and isinstance(data, dict):
        print(f"[updates] nodes={list(data.keys())}")
        return

    if chunk_type == "messages" and isinstance(data, tuple) and len(data) == 2:
        token, metadata = data
        node = metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
        content = getattr(token, "content", "")
        if isinstance(content, str) and content:
            print(f"[messages] node={node} token={content!r}")


def main() -> None:
    agent = create_stream_modes_agent()
    input_payload = {"messages": [{"role": "user", "content": "请查询上海当前天气。"}]}

    print("底层 stream（updates + messages, v2）：")
    for chunk in agent.stream(
        input_payload,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        if isinstance(chunk, dict):
            consume_v2_stream_chunk(chunk)

    print("\n最终 invoke 答复：")
    final_result = agent.invoke(input_payload)
    print(final_result["messages"][-1].content)


if __name__ == "__main__":
    main()
