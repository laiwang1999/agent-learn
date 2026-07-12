"""演示真实 Agent 的 stream_events(version='v3') 文本增量与最终 output。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from langchain.agents import create_agent

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


def _load_basic_tool_definition_module():
    """加载第 8 章天气工具，避免在本文件中重复定义 schema。"""
    module_path = (
        Path(__file__).parents[1] / "08-tools" / "basic_tool_definition.py"
    )
    spec = spec_from_file_location("basic_tool_definition", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


get_city_weather = _load_basic_tool_definition_module().get_city_weather


def create_streaming_weather_agent():
    """创建用于 event streaming 演示的天气 Agent。"""
    return create_agent(
        model=create_chat_model(),
        tools=[get_city_weather],
        system_prompt=(
            "你是天气助手。回答天气问题时必须调用 get_city_weather，禁止猜测天气事实。"
            "最终答复必须使用中文。"
        ),
        name="streaming_weather_agent",
    )


def main() -> None:
    agent = create_streaming_weather_agent()
    stream = agent.stream_events(
        {"messages": [{"role": "user", "content": "请查询上海当前天气。"}]},
        version="v3",
    )

    print("模型文本增量：", end="")
    for message in stream.messages:
        for delta in message.text:
            print(delta, end="", flush=True)
    print()

    for call in stream.tool_calls:
        print(f"工具执行：{call.tool_name} input={call.input}")

    final_state = stream.output
    print("最终消息数：", len(final_state["messages"]))
    print("最终答复：", final_state["messages"][-1].content)


if __name__ == "__main__":
    main()
